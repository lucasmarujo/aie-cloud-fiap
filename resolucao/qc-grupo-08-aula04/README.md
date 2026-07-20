# Como rodar — Pessoa 2 (N2 2.1 + N3 3.1)

Guia para testar o pipeline de reviews (N2 2.1) e o script de embeddings (N3 3.1).
Tudo pode ser executado no **Azure Cloud Shell** (bash) — sem instalação local.

---

## Ambiente: Azure Cloud Shell

No Cloud Shell você já está autenticada — **não precisa de `az login`**.
O `DefaultAzureCredential` pega automaticamente a identidade da sessão.

```bash
# Confirme que está na subscription certa
az account show --query "{nome:name, id:id}" -o table
```

Instale as dependências Python uma única vez por sessão:
```bash
pip install --user \
  azure-identity azure-storage-blob azure-cosmos \
  azure-search-documents azure-ai-textanalytics \
  openai
```

---

## Pré-requisitos — Terraform da Aula 4

Os scripts precisam dos recursos Azure já provisionados pelo terraform da Aula 4.
A pasta `terraform/` desta entrega é **standalone** — roda de onde está,
sem precisar copiar nada para a pasta do lab.

### 1. Obter variáveis do terraform da Aula 4

```bash
cd aulas/04-servicos-cognitivos/lab/terraform

export TF_VAR_resource_group_name=$(terraform output -raw resource_group_name)
export TF_VAR_function_app_name=$(terraform output -raw function_app_name)
export TF_VAR_sufixo=$(terraform output -raw sufixo)

# Para os scripts Python
export AI_ENDPOINT=$(terraform output -raw ai_endpoint)
export COSMOS_ACCOUNT_AULA2=$(terraform output -raw cosmos_account_name)
```

### 2. Aplicar o terraform desta entrega (provisiona Azure OpenAI)

```bash
cd resolucao/qc-grupo-08-aula04/terraform
terraform init
terraform apply
```

### 3. Exportar o endpoint do OpenAI

```bash
export AZURE_OPENAI_ENDPOINT=$(terraform output -raw openai_endpoint)
```

### 4. Variáveis da Aula 2

```bash
cd aulas/02-storage-bancos/lab/terraform
export STORAGE_ACCOUNT_NAME=$(terraform output -raw storage_account_name)
export COSMOS_ENDPOINT=$(terraform output -raw cosmos_endpoint)
export SEARCH_ENDPOINT=$(terraform output -raw search_endpoint)
```

---

## Ordem de execução completa

```
SETUP DA ESTRUTURA (scripts_dependencia_aula2/)
  1. python 1_upload_csv_blob.py      → sobe produtos.csv pro Blob
  2. python 2_popular_reviews.py      → popula 30 reviews no Cosmos
  3. python 3_indexar_produtos.py     → cria índice base no AI Search

N3 3.1 — EMBEDDINGS (scripts/)
  4. python gerar_embeddings_vector.py → adiciona vetores ao índice + compara buscas

N2 2.1 — PIPELINE DE REVIEWS (function/)
  5. func start  (ou deploy no Azure)  → sobe a Function
  6. curl /analisar-reviews            → roda o pipeline completo
```

---

## Passo 1–3: Subir a estrutura da Aula 2

```bash
cd resolucao/qc-grupo-08-aula04/scripts_dependencia_aula2

# 1. Blob
export STORAGE_ACCOUNT_NAME="<nome do storage>"
python 1_upload_csv_blob.py

# 2. Cosmos reviews
export COSMOS_ENDPOINT="https://<nome-cosmos>.documents.azure.com"
python 2_popular_reviews.py

# 3. AI Search (índice base sem vetores)
export SEARCH_ENDPOINT="https://<nome-search>.search.windows.net"
python 3_indexar_produtos.py
```

---

## Passo 4: N3 3.1 — Script de embeddings

O script é standalone — roda direto no terminal, sem Function.

```bash
cd resolucao/qc-grupo-08-aula04

export AZURE_OPENAI_ENDPOINT="https://openai-qc-XXXXXX.openai.azure.com/"
export STORAGE_ACCOUNT_NAME="<nome do storage>"
export SEARCH_ENDPOINT="https://srch-qc-XXXXXX.search.windows.net"

python scripts/gerar_embeddings_vector.py
```

### Saída esperada
```
→ 20 produtos lidos do Blob
→ Recriando índice 'produtos-index' com campo content_vector (1536 dim)
✓ Índice recriado com vector search + semantic search
→ Gerando embeddings e indexando 20 produtos...
  [01/20] Cadeira Ergonômica DXRacer
  ...
✓ 20 documentos re-indexados com embeddings

═══════════════════════════════════════
COMPARAÇÃO: Vector Search vs Semantic Search
═══════════════════════════════════════
Query: "cadeira para minha coluna ergonômica"
  Vector Search  → ['Cadeira Ergonômica DXRacer', ...]
  Semantic Search→ ['Cadeira Ergonômica DXRacer', ...]
...
Custo carga inicial (única vez): ~$10.00
Custo incremental/mês:           ~$0.02
```

---

## Passo 5–6: N2 2.1 — Pipeline de reviews (Function)

### Opção A — Testar no Azure (mais simples no Cloud Shell)

Deploy direto e testa com curl contra a URL do Azure:

```bash
cd resolucao/qc-grupo-08-aula04/function

# Instalar dependências no venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Deploy (precisa do nome da Function App criada pelo Terraform)
FUNC_APP=$(cd ../../../aulas/04-servicos-cognitivos/lab/terraform && terraform output -raw function_app_name)
func azure functionapp publish $FUNC_APP

# Testar
BASE_URL="https://$FUNC_APP.azurewebsites.net/api"
curl "$BASE_URL/health"
curl "$BASE_URL/analisar-reviews?limit=5" | python3 -m json.tool
```

### Opção B — Testar localmente no Cloud Shell com `func start`

O Cloud Shell expõe portas via **Web Preview** (botão no topo da tela, porta 7071).

```bash
# Instalar Azure Functions Core Tools
npm install -g azure-functions-core-tools@4 --unsafe-perm true

cd resolucao/qc-grupo-08-aula04/function
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Crie o arquivo `local.settings.json` (não é commitado):
```bash
cat > local.settings.json << EOF
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "AzureWebJobsFeatureFlags": "EnableWorkerIndexing",
    "AI_ENDPOINT": "$AI_ENDPOINT",
    "AI_REGION": "brazilsouth",
    "STORAGE_ACCOUNT_AULA2": "$STORAGE_ACCOUNT_NAME",
    "COSMOS_ACCOUNT_AULA2": "$COSMOS_ACCOUNT_AULA2",
    "AZURE_OPENAI_ENDPOINT": "$AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_DEPLOYMENT": "gpt-4o-mini",
    "COSMOS_DB": "qc-db",
    "COSMOS_CONTAINER_REVIEWS": "reviews"
  }
}
EOF

func start
```

No Cloud Shell, clique em **Web Preview → Configure → Port 7071** para acessar.
Ou teste pelo terminal em outra aba:

```bash
# Health check
curl http://localhost:7071/api/health | python3 -m json.tool

# Pipeline N2 2.1 (processa até 5 reviews não processadas do Cosmos)
curl "http://localhost:7071/api/analisar-reviews?limit=5" | python3 -m json.tool

# Rota 3.3 do Lucas (só funciona depois do 2.1 ter processado o produto_id)
curl "http://localhost:7071/api/sumarizar-reviews-produto?produto_id=5" | python3 -m json.tool
```

### Resposta esperada do /analisar-reviews
```json
{
  "total_processadas": 5,
  "positivas": 3,
  "negativas": 1,
  "neutras": 0,
  "mistas": 1,
  "exemplos": [
    {"id": "r-001", "sentimento": "positive", "aspectos_count": 2, "tem_resumo": false},
    {"id": "r-012", "sentimento": "mixed",    "aspectos_count": 4, "tem_resumo": true}
  ]
}
```

### Verificar schema no Cosmos após o pipeline
```bash
az cosmosdb sql query \
  --account-name $COSMOS_ACCOUNT_AULA2 \
  --resource-group <rg-aula2> \
  --database-name qc-db \
  --container-name reviews \
  --query-text "SELECT c.id, c.sentimento_label, c.aspectos, c.texto_redacted, c.resumo FROM c WHERE IS_DEFINED(c.texto_redacted)" \
  --output table
```

---

## Estrutura de arquivos desta entrega

```
resolucao/qc-grupo-08-aula04/
├── README.md                          ← este arquivo
├── respostas-pessoa2-aula04.md        ← documento de entrega (N2 2.1 + N3 3.1)
├── function/
│   ├── function_app.py                ← pipeline N2 2.1 + rota 3.3 (Lucas)
│   └── requirements.txt
├── terraform/
│   └── cognitive.tf                   ← Azure OpenAI + embeddings + gpt-4o-mini
├── scripts/
│   └── gerar_embeddings_vector.py     ← N3 3.1: embeddings + vector search
└── scripts_dependencia_aula2/         ← setup da estrutura base
    ├── data/produtos.csv
    ├── 1_upload_csv_blob.py
    ├── 2_popular_reviews.py
    └── 3_indexar_produtos.py
```

---

## Troubleshooting

| Erro | Causa | Solução |
|------|-------|---------|
| `AuthorizationFailure` em qualquer serviço | Role não propagou após `terraform apply` | Aguardar 2–3 min e tentar novamente |
| `ResourceNotFound` no Cosmos | Endpoint ou nome incorreto | Conferir `terraform output` e variáveis exportadas |
| `IndexNotFound` no AI Search | Passo 3 não rodou | Rodar `3_indexar_produtos.py` antes do script de embeddings |
| `DeploymentNotFound` no OpenAI | `terraform apply` não concluído | Verificar `terraform output openai_endpoint` |
| `begin_analyze_actions` lento | LRO com muitas reviews longas | Reduzir `?limit=3` nos primeiros testes |
| `func start` sem porta | Cloud Shell sem Web Preview | Usar Opção A (deploy no Azure) |
