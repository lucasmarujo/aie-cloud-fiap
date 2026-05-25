# Guia de Laboratório — Aula 4

**Tema:** Serviços Cognitivos & APIs
**Plataforma:** Microsoft Azure (Azure for Students)
**Ambiente:** **Azure Cloud Shell** — tudo no browser

---

## Visão geral do lab

```
Atividade 1 — Provisionar Azure AI Services + Function estendida     ~30 min  (L₁)
Atividade 2 — Speech-to-Text com áudio público (PT-BR)               ~45 min  (L₂)
Atividade 3 — Language: pipeline de reviews QC (Cosmos)              ~45 min  (L₃)
Atividade 4 — Vision: classificação + OCR de imagem de produto       ~20 min  (L₄)
Wrap-up   — terraform destroy + verificação custo zero               ~5 min
```

> **Regra de ouro:** `terraform destroy` ao final. AI Services no tier `S0` cobra **por chamada** — sem chamadas = sem custo.

---

## Pré-requisitos

- ✅ Aulas 1-3 concluídas
- ✅ **Storage e Cosmos da Aula 2 aplicados** (Blob com `produtos.csv`, Cosmos com reviews populadas)
- ✅ Repositório `aie-cloud` clonado no Cloud Shell

Se você destruiu a Aula 2:

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
SQL_PASSWORD=$(openssl rand -base64 24)
terraform apply -auto-approve -var="sql_admin_password=$SQL_PASSWORD"
# (e re-popular Cosmos com reviews via popular_reviews.py — ver guia da Aula 2)
```

---

## Preparação (5 min)

### Pegar outputs da Aula 2

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
export STORAGE_AULA2=$(terraform output -raw storage_account_name)
export RG_AULA2=$(terraform output -raw resource_group_name)
export COSMOS_AULA2=$(terraform output -raw cosmos_account_name)

echo "Storage: $STORAGE_AULA2"
echo "RG:      $RG_AULA2"
echo "Cosmos:  $COSMOS_AULA2"
```

### Criar workspace para arquivos baixados

A Aula 4 baixa áudio e imagem do mundo externo. Use uma pasta separada do clone do `aie-cloud`:

```bash
mkdir -p ~/qc-aula04
cd ~/qc-aula04
```

### Ir para o Terraform da Aula 4

```bash
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform
ls
# main.tf  variables.tf  outputs.tf  cognitive.tf  keyvault.tf  function.tf  README.md
```

Leia rapidamente os `.tf` ou o [README do Terraform](terraform/README.md).

---

## Atividade 1 — Provisionar Azure AI Services + Function

**Objetivo:** Provisionar um recurso multi-service do AI Services (1 endpoint para Speech, Language e Vision) e uma Function App com Managed Identity + 3 roles (AI/Blob/Cosmos).

### Passo 1 — Aplicar Terraform

```bash
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform

terraform init

terraform apply -auto-approve \
  -var="storage_account_aula2=$STORAGE_AULA2" \
  -var="resource_group_aula2=$RG_AULA2" \
  -var="cosmos_account_aula2=$COSMOS_AULA2"
```

Tempo: ~3-5 min (AI Services demora um pouco a propagar).

### Passo 2 — Exportar outputs

```bash
export AI_ENDPOINT=$(terraform output -raw ai_endpoint)
export KEY_VAULT_NAME=$(terraform output -raw key_vault_name)
export FUNC_NAME=$(terraform output -raw function_app_name)
export FUNC_HOSTNAME=$(terraform output -raw function_app_hostname)

echo "AI Services: $AI_ENDPOINT"
echo "Key Vault:   $KEY_VAULT_NAME"
echo "Function:    $FUNC_NAME"
```

### Passo 3 — Conferir o que foi provisionado

No portal Azure → Resource Group da Aula 4, você deve ver:

- 1 × Storage Account (estado da Function)
- 1 × App Service Plan (Y1)
- 1 × **Cognitive Services** (multi-service S0 com custom subdomain)
- 1 × **Key Vault** (com segredo `ai-services-key`)
- 1 × **Function App** (Python 3.11, Managed Identity SystemAssigned)

Em [cognitive.tf](terraform/cognitive.tf), observe **`custom_subdomain_name`** — é o que permite Managed Identity autenticar no AI Services.

**✅ Checkpoint L₁:** 5 recursos no Resource Group da Aula 4?

---

## Atividade 2 — Speech-to-Text com áudio PT-BR

**Objetivo:** Transcrever um trecho de áudio em PT-BR usando Azure Speech via Managed Identity (sem chave no código).

### Passo 1 — Obter um áudio em PT-BR

Você tem 2 opções:

**Opção A — Baixar um podcast público** (ex: BBC News Brasil):

```bash
cd ~/qc-aula04

PODCAST_URL="https://downloads.bbc.co.uk/podcasts/portuguese/global-news/audio-sample.mp3"
curl -L -o bbc-trecho.mp3 "$PODCAST_URL"
# Se a URL acima estiver indisponível, use Opção B.
```

**Opção B — Gerar áudio sintético com TTS** (usando o **mesmo AI Services** do lab):

```bash
pip install --user azure-cognitiveservices-speech azure-identity azure-keyvault-secrets

cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/scripts
python3 gerar_audio_tts.py
# Saída: ~/qc-aula04/audio-teste.wav

cd ~/qc-aula04
```

### Passo 2 — Upload do áudio no Blob da Aula 2

```bash
# Criar container 'audios' se ainda não existir
az storage container create \
  --account-name "$STORAGE_AULA2" \
  --name audios \
  --auth-mode login 2>/dev/null || true

# Upload
AUDIO_FILE=$(ls *.mp3 *.wav 2>/dev/null | head -1)
echo "Subindo: $AUDIO_FILE"

az storage blob upload \
  --account-name "$STORAGE_AULA2" \
  --container-name audios \
  --name "$AUDIO_FILE" \
  --file "$AUDIO_FILE" \
  --auth-mode login \
  --overwrite
```

### Passo 3 — Deploy da Function

A pasta [function/](function/) já tem o código consolidado com as 4 rotas (`/health`, `/transcrever`, `/analisar-reviews`, `/analisar-imagem`). Vamos fazer **um único deploy** com tudo:

```bash
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/function
func azure functionapp publish "$FUNC_NAME" --python
```

Tempo: ~2-3 min (Speech SDK + Vision SDK pesam um pouco).

### Passo 4 — Testar `/transcrever`

```bash
# Aguardar Managed Identity propagar (importante!)
sleep 90

# Health primeiro
curl -s "$FUNC_HOSTNAME/api/health" | python3 -m json.tool

# Transcrever
curl -s "$FUNC_HOSTNAME/api/transcrever?blob=$AUDIO_FILE" | python3 -m json.tool
```

Esperado: JSON com `"transcricao": "..."` em PT-BR coerente.

> **Erro comum:** "InvalidAuthenticationToken" — custom subdomain não habilitado ou MI ainda propagando. Aguarde 2 min. Se persistir, ver troubleshooting.

**✅ Checkpoint L₂:** Transcrição PT-BR retornou texto coerente?

---

## Atividade 3 — Language: pipeline de reviews da QC

**Objetivo:** Ler reviews do Cosmos (populadas na Aula 2), analisar sentimento + entidades via Language, e gravar os resultados de volta no Cosmos. **Tudo via MI**, sem chave no código.

### Passo 1 — Conferir a rota `/analisar-reviews`

Já está no [function_app.py](function/function_app.py) deployado no passo anterior. Ela:

1. Conecta no Cosmos via `DefaultAzureCredential`
2. Busca reviews ainda não processadas (`WHERE NOT IS_DEFINED(c.sentimento_label)`)
3. Chama `analyze_sentiment` e `recognize_entities` em batch
4. Faz `upsert_item` no Cosmos com novos campos

### Passo 2 — Rodar

```bash
curl -s -X POST "$FUNC_HOSTNAME/api/analisar-reviews?limit=10" | python3 -m json.tool
```

Esperado:

```json
{
  "total_analisadas": 10,
  "positivas": 6,
  "negativas": 3,
  "neutras":   1,
  "exemplos":  [...]
}
```

### Passo 3 — Validar no Cosmos

No portal → Cosmos DB da Aula 2 → **Data Explorer** → container `reviews`. Os documentos agora têm `sentimento_label`, `sentimento_score` e `entidades[]`.

**✅ Checkpoint L₃:** Reviews enriquecidas no Cosmos?

---

## Atividade 4 — Vision: classificação + OCR de imagem

**Objetivo:** Analisar uma imagem de produto da QC com Vision (tags + caption + OCR + objetos).

### Passo 1 — Subir uma imagem

```bash
cd ~/qc-aula04

# Baixar uma imagem livre (ex: cadeira no Unsplash)
curl -L -o cadeira-produto.jpg "https://images.unsplash.com/photo-1592078615290-033ee584e267?w=800"

# Criar container 'imagens' se ainda não existir
az storage container create \
  --account-name "$STORAGE_AULA2" \
  --name imagens \
  --auth-mode login 2>/dev/null || true

# Upload
az storage blob upload \
  --account-name "$STORAGE_AULA2" \
  --container-name imagens \
  --name cadeira-produto.jpg \
  --file cadeira-produto.jpg \
  --auth-mode login \
  --overwrite
```

### Passo 2 — Testar `/analisar-imagem`

```bash
curl -s "$FUNC_HOSTNAME/api/analisar-imagem?blob=cadeira-produto.jpg" | python3 -m json.tool
```

Esperado:

```json
{
  "caption": "uma cadeira em um quarto",
  "tags": [
    {"name": "chair",    "confidence": 0.98},
    {"name": "furniture","confidence": 0.96},
    ...
  ],
  "texto_extraido": "",
  "objetos_detectados": [{"label": "chair", "box": [...]}]
}
```

### Passo 3 — Validar no portal

Portal → AI Services da Aula 4 → **Quotas** ou **Metrics**: você deve ver requests recentes para Speech, Language e Vision.

**✅ Checkpoint L₄:** Imagem analisada com tags + caption?

---

## Wrap-up — Destroy e custo zero (5 min)

### Passo 1 — Destruir o ambiente da Aula 4

```bash
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform

terraform destroy -auto-approve \
  -var="storage_account_aula2=$STORAGE_AULA2" \
  -var="resource_group_aula2=$RG_AULA2" \
  -var="cosmos_account_aula2=$COSMOS_AULA2"
```

Tempo: ~2-3 min.

> Storage e Cosmos da Aula 2 NÃO são destruídos (são `data` source).

### Passo 2 — Decidir sobre a Aula 2

Próxima aula (MLOps) também usa o catálogo. Considere manter a Aula 2 aplicada por mais uma semana, ou destruir e re-aplicar antes da Aula 5.

### Passo 3 — Verificar custo

Portal → **Cost Management** → **Análise de custo** → filtrar por hoje. Esperado: < $0,50 (Speech Free Tier 5h/mês + AI Services S0 cobra só por uso real).

---

## Conexão com o projeto Quantum Commerce

A Function da QC agora tem **4 tools cognitivas** consumíveis pelos agentes:

```
GET  /api/produtos?categoria=...           (Aula 3) — busca no Blob via MI
GET  /api/transcrever?blob=...              (Aula 4) — Speech-to-Text
POST /api/analisar-reviews?limit=...        (Aula 4) — Language sentimento+entidades
GET  /api/analisar-imagem?blob=...          (Aula 4) — Vision tags+OCR+caption
```

Os agentes podem agora **ouvir** o cliente no atendimento por voz, **entender** o sentimento e as entidades das reviews, e **ver** as imagens dos produtos.

---

## Troubleshooting — Problemas comuns

| Problema | Causa | Solução |
|----------|-------|---------|
| MI falha — "InvalidAuthenticationToken" | Custom subdomain não configurado | Verificar `custom_subdomain_name` no `azurerm_cognitive_account` (já está, mas conferir TF aplicou) |
| Speech "Unauthorized" | Token AAD não funciona em SDKs antigos | Subir a versão de `azure-cognitiveservices-speech` no `requirements.txt` |
| `/analisar-reviews` retorna "Nenhuma review" | Aula 2 destruída ou Cosmos sem reviews | Re-aplicar TF da Aula 2 + rodar `popular_reviews.py` |
| Function timeout (>5 min) | Muitas reviews em batch | Reduzir `limit=5`; em produção, usar Queue trigger |
| Quota Speech esgotada | Free tier 5h/mês | Aguardar mês seguinte ou subir tier S0 |
| Vision OCR fraco em PT | Documentos manuscritos | Read API tem qualidade variável; testar com texto impresso |
| `curl` para `/transcrever` retorna 500 com `BlobNotFound` | Arquivo não foi subido ou nome diferente | `az storage blob list --account-name "$STORAGE_AULA2" --container-name audios --auth-mode login -o table` |
| Cosmos `Forbidden` | Role data plane não propagou | Aguardar 2 min; ou conceder via CLI: `az cosmosdb sql role assignment create --account-name ... --principal-id ... --role-definition-id 00000000-0000-0000-0000-000000000002 --scope "/"` |

---

## Referências

- [Azure AI Services — autenticação com Microsoft Entra ID](https://learn.microsoft.com/azure/ai-services/authentication?tabs=powershell)
- [Speech SDK Python](https://learn.microsoft.com/azure/ai-services/speech-service/quickstarts/setup-platform)
- [Language SDK Python](https://learn.microsoft.com/python/api/overview/azure/ai-textanalytics-readme)
- [Image Analysis SDK 4.0](https://learn.microsoft.com/azure/ai-services/computer-vision/how-to/call-analyze-image-40)
- [Custom subdomain — pré-requisito para MI](https://learn.microsoft.com/azure/ai-services/cognitive-services-custom-subdomains)
- [Terraform AzureRM Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
