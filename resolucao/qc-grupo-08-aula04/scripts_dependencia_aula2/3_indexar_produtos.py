"""
Passo 3 — Cria o índice base 'produtos-index' no AI Search e indexa os produtos
do Blob com semantic search (sem campo vetorial ainda).

Fonte: Aula 2 / Atividade 3-B (script original preservado sem alterações).
O campo vetorial (content_vector) será adicionado pelo script N3 3.1:
    ../scripts/gerar_embeddings_vector.py

Variáveis de ambiente:
    SEARCH_ENDPOINT       — terraform output -raw search_endpoint (Aula 2)
    STORAGE_ACCOUNT_NAME  — nome do Storage Account com produtos.csv

Dependências:
    pip install --user azure-identity azure-search-documents azure-storage-blob
"""

import csv
import os

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
)
from azure.storage.blob import BlobServiceClient

INDEX_NAME         = "produtos-index"
SEMANTIC_CFG       = "produtos-semantic-config"


def main():
    endpoint        = os.environ["SEARCH_ENDPOINT"]
    storage_account = os.environ["STORAGE_ACCOUNT_NAME"]
    credential      = DefaultAzureCredential()

    # 1. Criar índice com semantic search
    print(f"→ Criando índice '{INDEX_NAME}' em {endpoint}...")
    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)

    index = SearchIndex(
        name=INDEX_NAME,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="nome",     type=SearchFieldDataType.String, analyzer_name="pt-br.microsoft"),
            SearchableField(name="descricao",type=SearchFieldDataType.String, analyzer_name="pt-br.microsoft"),
            SimpleField(name="categoria",    type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(name="preco",        type=SearchFieldDataType.Double, filterable=True, sortable=True),
            SimpleField(name="estoque",      type=SearchFieldDataType.Int32,  filterable=True),
        ],
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
    print("✓ Índice criado")

    # 2. Baixar CSV do Blob e indexar
    print(f"→ Baixando produtos.csv de {storage_account}/catalogo...")
    blob_svc = BlobServiceClient(
        f"https://{storage_account}.blob.core.windows.net",
        credential=credential,
    )
    blob        = blob_svc.get_blob_client(container="catalogo", blob="produtos.csv")
    csv_content = blob.download_blob().readall().decode("utf-8")
    rows        = list(csv.DictReader(csv_content.splitlines()))

    documentos = [
        {
            "id":       r["id"],
            "nome":     r["nome"],
            "descricao":r["descricao"],
            "categoria":r["categoria"],
            "preco":    float(r["preco"]),
            "estoque":  int(r["estoque"]),
        }
        for r in rows
    ]

    search_client = SearchClient(endpoint=endpoint, index_name=INDEX_NAME, credential=credential)
    result = search_client.upload_documents(documents=documentos)
    print(f"✓ {len(result)} produtos indexados com semantic search")

    # 3. Teste rápido
    print("\n=== Busca semântica: 'algo para trabalhar em pé' ===")
    for doc in search_client.search(
        search_text="algo para trabalhar em pé",
        query_type="semantic",
        semantic_configuration_name=SEMANTIC_CFG,
        top=3,
    ):
        score = doc.get("@search.reranker_score", doc.get("@search.score"))
        print(f"  [{score:.2f}] {doc['nome']}")

    print("\nPróximo passo: python ../scripts/gerar_embeddings_vector.py")
    print("(adiciona o campo content_vector com embeddings reais ao mesmo índice)")


if __name__ == "__main__":
    main()
