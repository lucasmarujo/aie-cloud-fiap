"""
Exercício 3.3 — Benchmark: Cosmos vs SQL vs AI Search (Quantum Commerce)
=======================================================================

Compara TRÊS estratégias de busca de produto para a query do agente da QC:
  (a) Azure SQL  -> LIKE '%cadeira%' + filtros de categoria/preço   (full-text "pobre")
  (b) Cosmos DB  -> Cosmos NÃO tem full-text nativo. Aqui ilustramos a
                    abordagem de "fallback": varredura/CONTAINS no texto da
                    review como proxy de keyword search, deixando explícito
                    que produção exigiria indexar o conteúdo no AI Search.
  (c) Azure AI Search -> vector search (embeddings) + semantic ranking.

Mede latência (média e p95) rodando 10 queries por estratégia com
time.perf_counter() e imprime uma tabela comparativa no terminal.

DESIGN:
  - SEM segredos no código. Tudo via variáveis de ambiente + Managed Identity
    (DefaultAzureCredential). Roda no Azure Cloud Shell.
  - Cada backend é encapsulado num "Searcher" com a mesma interface .buscar(q),
    de modo que o agente de busca da QC poderia plugar qualquer um como TOOL.
  - Backends ausentes (env não configurado) são pulados com aviso — o script
    nunca quebra o benchmark inteiro por causa de um backend indisponível.

Pré-requisitos (Cloud Shell):
  pip install --user pyodbc azure-identity azure-cosmos \
                     azure-search-documents sentence-transformers

Variáveis de ambiente esperadas:
  # Azure SQL
  SQL_SERVER          ex: sql-qc-xxxx.database.windows.net
  SQL_DATABASE        ex: qcdb
  # Cosmos DB
  COSMOS_ENDPOINT     ex: https://cosmos-qc-xxxx.documents.azure.com:443/
  COSMOS_DATABASE     ex: qc
  COSMOS_CONTAINER    ex: reviews          (particionado por produto_id)
  # Azure AI Search
  SEARCH_ENDPOINT     ex: https://srch-qc-xxxx.search.windows.net
  SEARCH_INDEX        ex: produtos-vector-index  (criado no Ex 3.1)
"""

from __future__ import annotations

import os
import statistics
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from azure.identity import DefaultAzureCredential

# ----------------------------------------------------------------------------
# Configuração
# ----------------------------------------------------------------------------

# A pergunta-alvo do exercício. As 10 medições usam variações realistas que um
# agente/usuário faria — é assim que se mede latência média de forma honesta.
QUERY_ALVO = "cadeira ergonômica para dor lombar"

QUERIES_BENCH = [
    "cadeira ergonômica para dor lombar",
    "cadeira boa para minha coluna",
    "preciso de uma cadeira que apoie as costas",
    "cadeira de escritório com apoio lombar",
    "assento confortável para trabalhar sentado o dia todo",
    "cadeira gamer ergonômica",
    "cadeira que não dói as costas",
    "suporte para postura no home office",
    "cadeira ajustável para problema na lombar",
    "melhor cadeira para quem tem hérnia de disco",
]

# Modelo de embedding usado no Ex 3.1 (mesmo índice produtos-vector-index).
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384-dim, roda local no Cloud Shell

# Token scope para autenticar no Azure SQL com AAD/Managed Identity.
SQL_TOKEN_SCOPE = "https://database.windows.net/.default"


# ----------------------------------------------------------------------------
# Resultado de uma busca (interface comum a todos os backends)
# ----------------------------------------------------------------------------

@dataclass
class Hit:
    nome: str
    score: float = 0.0


@dataclass
class BenchResult:
    nome: str
    latencias_ms: list[float] = field(default_factory=list)
    top_hits: list[Hit] = field(default_factory=list)  # resultado da QUERY_ALVO
    erro: Optional[str] = None

    @property
    def media_ms(self) -> float:
        return statistics.mean(self.latencias_ms) if self.latencias_ms else float("nan")

    @property
    def p95_ms(self) -> float:
        if not self.latencias_ms:
            return float("nan")
        ordenado = sorted(self.latencias_ms)
        # índice p95 sobre 10 amostras -> 9º elemento (0-based: 8)
        idx = max(0, int(round(0.95 * len(ordenado))) - 1)
        return ordenado[idx]


# ----------------------------------------------------------------------------
# (a) Azure SQL — LIKE + filtros
# ----------------------------------------------------------------------------

class SqlSearcher:
    """
    Busca por palavra-chave em T_PRODUTOS via LIKE '%termo%'.

    Limitação fundamental (relevante para a comparação de QUALIDADE):
    LIKE é matching de SUBSTRING literal. A query "cadeira ergonômica para dor
    lombar" só casa se a string aparecer textualmente em nome/descricao. Não há
    nenhuma noção de semântica — "apoio para coluna" NÃO casa com "lombar".
    Por isso extraímos um termo-chave grosseiro (a primeira palavra "substantiva")
    e aplicamos filtros de categoria/preço, exatamente como o enunciado pede.
    """

    def __init__(self, credential: DefaultAzureCredential):
        import pyodbc  # import tardio: só falha se SQL for de fato usado

        self._pyodbc = pyodbc
        server = os.environ["SQL_SERVER"]
        database = os.environ["SQL_DATABASE"]

        # Token AAD via Managed Identity — sem usuário/senha no código.
        token = credential.get_token(SQL_TOKEN_SCOPE).token.encode("utf-16-le")
        # 1256 = SQL_COPT_SS_ACCESS_TOKEN (driver msodbcsql18)
        token_struct = struct_token(token)

        conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={server};DATABASE={database};"
            "Encrypt=yes;TrustServerCertificate=no;"
        )
        self._conn = pyodbc.connect(conn_str, attrs_before={1256: token_struct})

    @staticmethod
    def _termo_chave(query: str) -> str:
        # Heurística simples: pega o primeiro substantivo "forte" da query.
        # Numa busca LIKE real você não tem como extrair semântica — isto já é
        # generoso. Para a QUERY_ALVO, o termo será "cadeira".
        stop = {"para", "de", "com", "que", "uma", "um", "o", "a", "boa", "minha"}
        for tok in query.lower().split():
            tok = tok.strip(",.")
            if tok not in stop and len(tok) > 3:
                return tok
        return query.split()[0]

    def buscar(self, query: str, categoria: Optional[str] = None,
               preco_max: Optional[float] = None) -> list[Hit]:
        termo = self._termo_chave(query)
        sql = (
            "SELECT TOP 3 nome, preco FROM T_PRODUTOS "
            "WHERE (nome LIKE ? OR descricao LIKE ?)"
        )
        params: list = [f"%{termo}%", f"%{termo}%"]
        if categoria:
            sql += " AND categoria = ?"
            params.append(categoria)
        if preco_max is not None:
            sql += " AND preco <= ?"
            params.append(preco_max)
        sql += " ORDER BY preco ASC"

        cur = self._conn.cursor()
        cur.execute(sql, params)
        return [Hit(nome=row[0], score=0.0) for row in cur.fetchall()]


def struct_token(token: bytes) -> bytes:
    """Empacota o access token AAD no formato esperado pelo ODBC (len + bytes)."""
    import struct
    return struct.pack(f"<I{len(token)}s", len(token), token)


# ----------------------------------------------------------------------------
# (b) Cosmos DB — "full-text" via CONTAINS (PROXY: Cosmos não tem full-text nativo)
# ----------------------------------------------------------------------------

class CosmosSearcher:
    """
    O enunciado deixa claro: Cosmos NÃO tem índice full-text nativo. O que
    existe é a função CONTAINS() em SQL-API, que faz matching de substring
    (case-sensitive por padrão) e, crucialmente, NÃO usa índice de texto:
    é varredura — RU/s explode em containers grandes e a relevância é nula
    (mesma limitação do LIKE, só que muito mais caro por RU).

    Implementamos aqui sobre o container `reviews` (texto livre das reviews,
    particionado por produto_id) apenas para MEDIR a abordagem e mostrar que
    ela é tecnicamente possível porém inadequada. A conclusão arquitetural é
    que, para busca textual real, o conteúdo precisa ser indexado num serviço
    externo — Azure AI Search — ao lado do Cosmos.
    """

    def __init__(self, credential: DefaultAzureCredential):
        from azure.cosmos import CosmosClient

        endpoint = os.environ["COSMOS_ENDPOINT"]
        db_name = os.environ["COSMOS_DATABASE"]
        container_name = os.environ.get("COSMOS_CONTAINER", "reviews")

        client = CosmosClient(endpoint, credential=credential)
        db = client.get_database_client(db_name)
        self._container = db.get_container_client(container_name)

    def buscar(self, query: str) -> list[Hit]:
        termo = SqlSearcher._termo_chave(query)
        # CONTAINS cross-partition: cara e sem ranking semântico, só substring.
        sql = (
            "SELECT TOP 3 c.produto_id, c.conteudo FROM c "
            "WHERE CONTAINS(c.conteudo, @termo, true)"
        )
        items = list(self._container.query_items(
            query=sql,
            parameters=[{"name": "@termo", "value": termo}],
            enable_cross_partition_query=True,
        ))
        return [Hit(nome=str(i.get("produto_id", "?")), score=0.0) for i in items]


# ----------------------------------------------------------------------------
# (c) Azure AI Search — vector + semantic ranking
# ----------------------------------------------------------------------------

class SearchSearcher:
    """
    A estratégia correta para o agente de busca (RAG). Reaproveita o índice
    `produtos-vector-index` do Ex 3.1: gera o embedding da query com o mesmo
    modelo (all-MiniLM-L6-v2, 384-dim) e faz vector search (HNSW) sobre o campo
    content_vector. Captura semântica — "dor lombar" recupera "apoio para a
    coluna" mesmo sem coincidência de palavras.
    """

    def __init__(self, credential: DefaultAzureCredential):
        from azure.search.documents import SearchClient
        from sentence_transformers import SentenceTransformer

        endpoint = os.environ["SEARCH_ENDPOINT"]
        index = os.environ.get("SEARCH_INDEX", "produtos-vector-index")

        self._client = SearchClient(endpoint=endpoint, index_name=index,
                                    credential=credential)
        # O modelo é carregado UMA vez no __init__ — não conta na latência de busca.
        self._model = SentenceTransformer(EMBEDDING_MODEL)

    def buscar(self, query: str) -> list[Hit]:
        q_vec = self._model.encode(query).tolist()
        results = self._client.search(
            search_text=None,
            vector_queries=[{
                "kind": "vector",
                "vector": q_vec,
                "k_nearest_neighbors": 3,
                "fields": "content_vector",
            }],
            top=3,
        )
        return [Hit(nome=r["nome"], score=float(r.get("@search.score", 0.0)))
                for r in results]


# ----------------------------------------------------------------------------
# Runner do benchmark
# ----------------------------------------------------------------------------

def medir(nome: str, fn_buscar: Callable[[str], list[Hit]]) -> BenchResult:
    """Roda as 10 queries, cronometra cada uma e guarda o top-hit da QUERY_ALVO."""
    res = BenchResult(nome=nome)
    try:
        # Warm-up: primeira chamada paga JIT/conexão/cache; não entra na média.
        fn_buscar(QUERY_ALVO)

        for q in QUERIES_BENCH:
            t0 = time.perf_counter()
            hits = fn_buscar(q)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            res.latencias_ms.append(dt_ms)
            if q == QUERY_ALVO:
                res.top_hits = hits
    except Exception as exc:  # noqa: BLE001 — queremos seguir com os outros backends
        res.erro = f"{type(exc).__name__}: {exc}"
    return res


def main() -> None:
    credential = DefaultAzureCredential()

    # Constrói só os backends configurados via env — os demais são pulados.
    backends: list[tuple[str, Callable[[], object]]] = [
        ("Azure SQL (LIKE)", lambda: SqlSearcher(credential)),
        ("Cosmos DB (CONTAINS)", lambda: CosmosSearcher(credential)),
        ("AI Search (vector)", lambda: SearchSearcher(credential)),
    ]

    resultados: list[BenchResult] = []
    for nome, factory in backends:
        try:
            searcher = factory()
        except KeyError as e:
            print(f"[SKIP] {nome}: variável de ambiente ausente {e}")
            continue
        except Exception as e:  # noqa: BLE001
            print(f"[SKIP] {nome}: falha ao inicializar -> {e}")
            continue
        print(f"[RUN ] {nome} ...")
        resultados.append(medir(nome, searcher.buscar))

    imprimir_relatorio(resultados)


def imprimir_relatorio(resultados: list[BenchResult]) -> None:
    print("\n" + "=" * 72)
    print(f"BENCHMARK — query alvo: {QUERY_ALVO!r}  ({len(QUERIES_BENCH)} queries)")
    print("=" * 72)
    print(f"{'Opção':<24}{'Média (ms)':>12}{'p95 (ms)':>12}   Top-1 da query alvo")
    print("-" * 72)
    for r in resultados:
        if r.erro:
            print(f"{r.nome:<24}{'ERRO':>12}{'':>12}   {r.erro}")
            continue
        top = r.top_hits[0].nome if r.top_hits else "(sem resultado)"
        print(f"{r.nome:<24}{r.media_ms:>12.1f}{r.p95_ms:>12.1f}   {top}")
    print("=" * 72)
    print("Latências medidas com time.perf_counter(); warm-up descartado.")


if __name__ == "__main__":
    main()
