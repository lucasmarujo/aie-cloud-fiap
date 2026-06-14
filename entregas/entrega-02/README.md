# Entrega Aula 02 — Grupo 08 — Como rodar

Artefatos do **Nível 3 (bônus)** desta entrega. Tudo roda no **Azure Cloud Shell** (política "no install" — só `pip install --user`). Documento principal: [`entrega-grupo-aula02.md`](entrega-grupo-aula02.md).

## Pré-requisitos

```bash
az login                          # já autenticado no Cloud Shell
pip install --user sentence-transformers azure-search-documents \
    azure-storage-blob azure-identity azure-cosmos pyodbc
```

Variáveis de ambiente esperadas (ajuste aos seus recursos do lab):

```bash
export STORAGE_ACCOUNT_NAME="stqc<sufixo>"        # conta de storage do lab (catálogo)
export STORAGE_ACCOUNT_LAKE="stqclake<sufixo>"    # conta ADLS Gen2 do synapse.tf (HNS)
export SEARCH_ENDPOINT="https://srch-qc-<sufixo>.search.windows.net"
export SQL_SERVER="sqlsrv-qc-<sufixo>.database.windows.net"
export SQL_DATABASE="qcdb"
export COSMOS_ENDPOINT="https://cosmos-qc-<sufixo>.documents.azure.com:443/"
```

A autenticação é **100% via Managed Identity** (`DefaultAzureCredential`) — nenhum script tem segredo hardcoded.

---

## Exercício 3.1 — Vector search verdadeira

```bash
python3 scripts/gerar_embeddings_vector.py
```

Lê `catalogo/produtos.csv`, gera embeddings com `all-MiniLM-L6-v2`, cria o índice
`produtos-vector-index` (campo `content_vector`, HNSW, 384 dims) no AI Search e roda
3 queries de vector search. **Requer AI Search SKU Basic+** (o Free não suporta campo vetorial).

> ⚠️ O `sentence-transformers` baixa ~80 MB de modelo no primeiro uso (vai para `~/.cache`).

## Exercício 3.2 — Synapse Serverless

```bash
# 1) Provisionar o Synapse Workspace + Lake (HNS)
cd ../../aulas/02-storage-bancos/lab/terraform   # ou onde estiver seu main.tf
# copie terraform/synapse.tf para junto do main.tf do lab, declare a variável e aplique:
terraform apply -var="sql_admin_password=<senha-forte>"

# 2) Gerar e subir os CSVs de logs
cd -                                              # voltar para entrega-02/
python3 scripts/gerar_logs_compras.py --upload --account "$STORAGE_ACCOUNT_LAKE"

# 3) No Synapse Studio → Serverless SQL Pool, rodar a query OPENROWSET
#    (SQL completo na seção 3.2 do entrega-grupo-aula02.md)
```

A variável `sql_admin_password` é **sensitive** — passe via `-var` na CLI ou `TF_VAR_sql_admin_password`, **nunca** commite em `.tfvars`.

## Exercício 3.3 — Benchmark SQL × Cosmos × AI Search

```bash
python3 scripts/benchmark_busca.py
```

Roda a query `"cadeira ergonômica para dor lombar"` nas 3 estratégias, mede latência
(média + p95 sobre 10 execuções, warm-up descartado) e imprime a tabela comparativa.

---

## Limpeza (evitar custo)

```bash
terraform destroy -var="sql_admin_password=<senha>"   # remove Synapse + Lake
# ou, para zerar tudo do lab:
az group delete --name rg-qc-<sufixo> --yes --no-wait
```

> **Não incluir no ZIP:** `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`, `~/.cache` do modelo.
