"""
Exercício 3.1 — Vector search VERDADEIRA no Azure AI Search (Quantum Commerce).

Diferença para o lab (indexar_produtos.py, que usa SEMANTIC ranking):
    aqui geramos EMBEDDINGS densos de "nome + descricao" com sentence-transformers
    (all-MiniLM-L6-v2, 384 dims), criamos um índice com campo vetorial HNSW e rodamos
    busca por similaridade de cosseno (kNN). É a base do RAG dos agentes da QC: o agente
    transforma a query do cliente no MESMO espaço vetorial e recupera os SKUs vizinhos.

Pré-requisitos (Azure Cloud Shell — política "no install", só --user):
    pip install --user azure-identity azure-search-documents azure-storage-blob \
        sentence-transformers

    O AI Search precisa estar em SKU >= Basic. O SKU Free do lab NÃO suporta
    campos vetoriais / vectorSearch — esse é o motivo de o lab ter ficado no
    semantic search. Promover para Basic é pré-requisito desta entrega.

Variáveis de ambiente (NUNCA hardcodar segredos):
    SEARCH_ENDPOINT       — terraform output -raw search_endpoint
    STORAGE_ACCOUNT_NAME  — Storage Account que contém catalogo/produtos.csv

Autenticação: DefaultAzureCredential (Managed Identity no Cloud Shell / az login local).
A MI precisa das roles "Search Index Data Contributor" + "Search Service Contributor"
no AI Search e "Storage Blob Data Reader" no Storage.
"""

from __future__ import annotations

import csv
import os

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery
from azure.storage.blob import BlobServiceClient
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
INDEX_NAME = "produtos-vector-index"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 dims, multilingual-fraco mas leve
EMBEDDING_DIMS = 384
HNSW_CONFIG = "hnsw-config"
VECTOR_PROFILE = "vector-profile"

# Queries em linguagem natural exigidas pelo enunciado (Parte A).
QUERIES = [
    "preciso de uma cadeira boa para minha coluna",
    "algo para acompanhar séries",
    "presente para um amigo que ama café",
]


def build_index_client(endpoint: str, credential) -> SearchIndexClient:
    return SearchIndexClient(endpoint=endpoint, credential=credential)


def criar_indice_vetorial(index_client: SearchIndexClient) -> None:
    """Cria o índice com campo content_vector (HNSW + similaridade de cosseno)."""
    index = SearchIndex(
        name=INDEX_NAME,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
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
            SimpleField(
                name="categoria",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
            ),
            SimpleField(
                name="preco",
                type=SearchFieldDataType.Double,
                filterable=True,
                sortable=True,
            ),
            # Campo VETORIAL: é onde mora o embedding de "nome + descricao".
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=EMBEDDING_DIMS,
                vector_search_profile_name=VECTOR_PROFILE,
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name=HNSW_CONFIG,
                    parameters=HnswParameters(
                        # m / ef_construction controlam recall vs. custo de build;
                        # cosine é a métrica natural para embeddings normalizados.
                        m=4,
                        ef_construction=400,
                        ef_search=500,
                        metric=VectorSearchAlgorithmMetric.COSINE,
                    ),
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name=VECTOR_PROFILE,
                    algorithm_configuration_name=HNSW_CONFIG,
                )
            ],
        ),
    )

    try:
        index_client.delete_index(INDEX_NAME)
    except Exception:
        pass  # índice ainda não existe na primeira execução
    index_client.create_index(index)
    print(f"✓ Índice vetorial '{INDEX_NAME}' criado ({EMBEDDING_DIMS} dims, HNSW/cosine)")


def carregar_produtos(storage_account: str, credential) -> list[dict]:
    """Baixa catalogo/produtos.csv do Blob e devolve a lista de dicts."""
    blob_client = BlobServiceClient(
        f"https://{storage_account}.blob.core.windows.net",
        credential=credential,
    )
    blob = blob_client.get_blob_client(container="catalogo", blob="produtos.csv")
    csv_content = blob.download_blob().readall().decode("utf-8")
    return list(csv.DictReader(csv_content.splitlines()))


def main() -> None:
    endpoint = os.environ["SEARCH_ENDPOINT"]
    storage_account = os.environ["STORAGE_ACCOUNT_NAME"]
    credential = DefaultAzureCredential()

    # 1. Modelo de embeddings (baixa ~80MB na 1ª execução; fica em cache no Cloud Shell).
    print(f"→ Carregando modelo de embeddings '{EMBEDDING_MODEL}'...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # 2. Índice vetorial
    index_client = build_index_client(endpoint, credential)
    criar_indice_vetorial(index_client)

    # 3. Produtos + geração de embeddings de "nome + descricao"
    rows = carregar_produtos(storage_account, credential)
    textos = [f"{r['nome']}. {r['descricao']}" for r in rows]
    # normalize_embeddings=True => vetores unitários, ideal para cosine.
    vetores = model.encode(
        textos, normalize_embeddings=True, show_progress_bar=True
    )

    documentos = [
        {
            "id": r["id"],
            "nome": r["nome"],
            "descricao": r["descricao"],
            "categoria": r["categoria"],
            "preco": float(r["preco"]),
            "content_vector": vetor.tolist(),
        }
        for r, vetor in zip(rows, vetores)
    ]

    search_client = SearchClient(
        endpoint=endpoint, index_name=INDEX_NAME, credential=credential
    )
    result = search_client.upload_documents(documents=documentos)
    print(f"✓ {len(result)} produtos indexados com embeddings")

    # 4. Vector search com as 3 queries em linguagem natural
    for query in QUERIES:
        # MESMO modelo + MESMA normalização que usamos para indexar — crucial.
        q_vec = model.encode(query, normalize_embeddings=True).tolist()
        vector_query = VectorizedQuery(
            vector=q_vec, k_nearest_neighbors=3, fields="content_vector"
        )
        print(f"\n=== Vector search: '{query}' ===")
        results = search_client.search(
            search_text=None,  # busca puramente vetorial (kNN), sem termos léxicos
            vector_queries=[vector_query],
            select=["nome", "categoria", "preco"],
            top=3,
        )
        for doc in results:
            # @search.score em busca vetorial = similaridade (0..1) na escala do AI Search.
            print(
                f"  [{doc['@search.score']:.3f}] {doc['nome']} "
                f"({doc['categoria']}) — R$ {doc['preco']:.2f}"
            )


if __name__ == "__main__":
    main()
