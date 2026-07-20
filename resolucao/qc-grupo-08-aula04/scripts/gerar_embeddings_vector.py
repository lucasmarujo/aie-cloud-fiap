"""
N3 3.1 — Vector Search real com Azure OpenAI (text-embedding-3-small, 1536 dim)

Tarefa:
  1. Lê os 20 produtos do Blob (produtos.csv da Aula 2)
  2. Gera embedding de "nome + descricao" para cada produto via Azure OpenAI
  3. Re-indexa no AI Search (índice da Aula 2) adicionando o campo content_vector
  4. Roda 3 queries semânticas e compara resultados

Pré-requisitos:
  - Azure OpenAI provisionado (cognitive.tf desta entrega)
  - AI Search e Blob da Aula 2 ainda existindo
  - Role "Cognitive Services OpenAI User" atribuída à sua identidade de Cloud Shell

Variáveis de ambiente:
  AZURE_OPENAI_ENDPOINT   — terraform output -raw openai_endpoint
  STORAGE_ACCOUNT_NAME    — terraform output -raw storage_account_name (Aula 2)
  SEARCH_ENDPOINT         — terraform output -raw search_endpoint (Aula 2)

Instalar dependências no Cloud Shell:
  pip install --user azure-identity azure-storage-blob azure-search-documents openai
"""

import csv
import os

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery
from azure.storage.blob import BlobServiceClient
from openai import AzureOpenAI

# ── Configuração ──────────────────────────────────────────────────────────────
INDEX_NAME         = "produtos-index"
SEMANTIC_CFG       = "produtos-semantic-config"
EMBEDDING_MODEL    = "text-embedding-3-small"
EMBEDDING_DIMS     = 1536
BLOB_CONTAINER     = "catalogo"
BLOB_ARQUIVO       = "produtos.csv"

OPENAI_ENDPOINT    = os.environ["AZURE_OPENAI_ENDPOINT"]
STORAGE_ACCOUNT    = os.environ["STORAGE_ACCOUNT_NAME"]
SEARCH_ENDPOINT    = os.environ["SEARCH_ENDPOINT"]

credential     = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)
openai_client = AzureOpenAI(
    azure_endpoint=OPENAI_ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version="2024-10-21",
)


# ── 1. Ler produtos.csv do Blob ───────────────────────────────────────────────
def ler_produtos() -> list[dict]:
    blob_svc = BlobServiceClient(
        f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=credential,
    )
    blob = blob_svc.get_blob_client(container=BLOB_CONTAINER, blob=BLOB_ARQUIVO)
    conteudo = blob.download_blob().readall().decode("utf-8")
    rows = list(csv.DictReader(conteudo.splitlines()))
    print(f"→ {len(rows)} produtos lidos do Blob")
    return rows


# ── 2. Gerar embedding de um texto via Azure OpenAI ───────────────────────────
def gerar_embedding(texto: str) -> list[float]:
    response = openai_client.embeddings.create(
        input=texto,
        model=EMBEDDING_MODEL,
    )
    return response.data[0].embedding


# ── 3. Recriar índice com campo content_vector ────────────────────────────────
def criar_indice_vector(index_client: SearchIndexClient) -> None:
    print(f"→ Recriando índice '{INDEX_NAME}' com campo content_vector (1536 dim)...")

    index = SearchIndex(
        name=INDEX_NAME,
        fields=[
            SimpleField(name="id",       type=SearchFieldDataType.String, key=True),
            SearchableField(
                name="nome",
                type=SearchFieldDataType.String,
                analyzer_name="pt-br.microsoft",
            ),
            SearchableField(
                name="descricao",
                type=SearchFieldDataType.String,
                analyzer_name="pt-br.microsoft",
            ),
            SimpleField(name="categoria", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(name="preco",     type=SearchFieldDataType.Double, filterable=True, sortable=True),
            SimpleField(name="estoque",   type=SearchFieldDataType.Int32,  filterable=True),
            # Campo vetorial: text-embedding-3-small → 1536 dimensões
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=EMBEDDING_DIMS,
                vector_search_profile_name="hnsw-profile",
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw-algo")],
            profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw-algo")],
        ),
        semantic_search=SemanticSearch(
            configurations=[
                SemanticConfiguration(
                    name=SEMANTIC_CFG,
                    prioritized_fields=SemanticPrioritizedFields(
                        title_field=SemanticField(field_name="nome"),
                        content_fields=[SemanticField(field_name="descricao")],
                        keywords_fields=[SemanticField(field_name="categoria")],
                    ),
                )
            ]
        ),
    )

    try:
        index_client.delete_index(INDEX_NAME)
    except Exception:
        pass
    index_client.create_index(index)
    print("✓ Índice recriado com vector search + semantic search")


# ── 4. Indexar produtos com embeddings ───────────────────────────────────────
def indexar_com_embeddings(produtos: list[dict], search_client: SearchClient) -> None:
    print(f"\n→ Gerando embeddings e indexando {len(produtos)} produtos...")
    documentos = []
    for i, p in enumerate(produtos):
        texto_para_embed = f"{p['nome']}. {p['descricao']}"
        embedding = gerar_embedding(texto_para_embed)
        documentos.append({
            "id":             p["id"],
            "nome":           p["nome"],
            "descricao":      p["descricao"],
            "categoria":      p["categoria"],
            "preco":          float(p["preco"]),
            "estoque":        int(p["estoque"]),
            "content_vector": embedding,
        })
        print(f"  [{i+1:02d}/20] {p['nome'][:45]}")

    result = search_client.upload_documents(documents=documentos)
    print(f"✓ {len(result)} documentos re-indexados com embeddings")


# ── 5. Rodar queries e comparar vector vs semantic ───────────────────────────
QUERIES = [
    "cadeira para minha coluna ergonômica",
    "notebook leve para trabalhar em viagens",
    "eletrodoméstico para fazer café rápido",
]


def query_vector(search_client: SearchClient, texto: str) -> list[str]:
    emb = gerar_embedding(texto)
    vq = VectorizedQuery(vector=emb, k_nearest_neighbors=3, fields="content_vector")
    results = search_client.search(search_text=None, vector_queries=[vq], top=3)
    return [r["nome"] for r in results]


def query_semantic(search_client: SearchClient, texto: str) -> list[str]:
    results = search_client.search(
        search_text=texto,
        query_type="semantic",
        semantic_configuration_name=SEMANTIC_CFG,
        top=3,
    )
    return [r["nome"] for r in results]


def comparar_buscas(search_client: SearchClient) -> None:
    print("\n" + "═" * 65)
    print("COMPARAÇÃO: Vector Search vs Semantic Search")
    print("═" * 65)

    for query in QUERIES:
        vec_results  = query_vector(search_client, query)
        sem_results  = query_semantic(search_client, query)

        print(f"\nQuery: \"{query}\"")
        print(f"  Vector Search  → {vec_results}")
        print(f"  Semantic Search→ {sem_results}")

    print("\n" + "═" * 65)
    print("Análise:")
    print("  Vector Search usa a distância cosseno entre embeddings.")
    print("  Semantic Search usa o re-ranker do AI Search (cross-encoder).")
    print("  Para jargão técnico e sinônimos (ex: 'coluna' → 'lombar'),")
    print("  o Vector Search tende a ser mais preciso pois captura semântica")
    print("  latente sem depender de correspondência de tokens.")
    print("═" * 65)


# ── 6. Custo estimado ─────────────────────────────────────────────────────────
def imprimir_custo() -> None:
    print("\n" + "─" * 65)
    print("CUSTO ESTIMADO — 5M produtos (text-embedding-3-small)")
    print("─" * 65)
    tokens_por_produto = 100
    total_tokens       = 5_000_000 * tokens_por_produto  # 500M tokens
    preco_por_milhao   = 0.02                             # USD/1M tokens
    custo_total        = (total_tokens / 1_000_000) * preco_por_milhao

    print(f"  Média tokens/produto (nome + descricao): ~{tokens_por_produto} tokens")
    print(f"  Total tokens (5M produtos):              {total_tokens:,.0f} tokens")
    print(f"  Preço text-embedding-3-small:            ${preco_por_milhao}/1M tokens")
    print(f"  Custo carga inicial (única vez):         ~${custo_total:.2f}")
    print()
    print("  Atualização incremental (10k novos produtos/mês):")
    tokens_inc = 10_000 * tokens_por_produto
    custo_inc  = (tokens_inc / 1_000_000) * preco_por_milhao
    print(f"    Tokens/mês:  {tokens_inc:,.0f} tokens")
    print(f"    Custo/mês:  ~${custo_inc:.4f} (praticamente zero)")
    print()
    print("  Estratégia de atualização incremental:")
    print("    - Event Grid monitora container 'catalogo' no Blob")
    print("    - Novo produto/csv → dispara Azure Function")
    print("    - Function gera embedding apenas do produto novo")
    print("    - Upsert no AI Search pelo campo 'id' (idempotente)")
    print("    - Re-embed de produto existente só quando descricao muda")
    print("─" * 65)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    index_client  = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=credential)
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=credential,
    )

    produtos = ler_produtos()
    criar_indice_vector(index_client)
    indexar_com_embeddings(produtos, search_client)
    comparar_buscas(search_client)
    imprimir_custo()


if __name__ == "__main__":
    main()
