"""
Passo 1 — Sobe o produtos.csv para o Blob Storage (container 'catalogo').

Execute este script se o blob da Aula 2 não existir mais ou se você quiser
recriar o container com os dados originais.

Variáveis de ambiente:
    STORAGE_ACCOUNT_NAME  — nome do Storage Account da Aula 2

Dependências:
    pip install --user azure-identity azure-storage-blob

Autenticação: DefaultAzureCredential (Cloud Shell já autenticado; fora do
Cloud Shell rode `az login` antes).
"""

import os
import pathlib

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient

STORAGE_ACCOUNT = os.environ["STORAGE_ACCOUNT_NAME"]
CONTAINER       = "catalogo"
BLOB_NAME       = "produtos.csv"
CSV_PATH        = pathlib.Path(__file__).parent / "data" / "produtos.csv"

credential  = DefaultAzureCredential()
blob_svc    = BlobServiceClient(
    f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=credential,
)


def garantir_container(client: BlobServiceClient) -> ContainerClient:
    ctr = client.get_container_client(CONTAINER)
    try:
        ctr.get_container_properties()
        print(f"→ Container '{CONTAINER}' já existe")
    except Exception:
        ctr.create_container()
        print(f"✓ Container '{CONTAINER}' criado")
    return ctr


def upload_csv(ctr: ContainerClient) -> None:
    with open(CSV_PATH, "rb") as f:
        ctr.upload_blob(name=BLOB_NAME, data=f, overwrite=True)
    print(f"✓ '{BLOB_NAME}' enviado para '{CONTAINER}' em {STORAGE_ACCOUNT}")


if __name__ == "__main__":
    ctr = garantir_container(blob_svc)
    upload_csv(ctr)
    print("\nPróximo passo: python 2_popular_reviews.py")
