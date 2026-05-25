# Function code — Aula 4

API HTTP da QC com **4 rotas cognitivas**, autenticadas por Managed Identity:

| Rota | Atividade do lab | Capacidade |
|------|-------------------|------------|
| `GET /api/health` | — | Status + lista de rotas |
| `GET /api/transcrever?blob=...&container=audios&idioma=pt-BR` | L₂ | Speech-to-Text |
| `POST /api/analisar-reviews?limit=10` | L₃ | Language: sentimento + entidades das reviews do Cosmos |
| `GET /api/analisar-imagem?blob=...&container=imagens` | L₄ | Vision: tags + OCR + caption |

## Pré-requisitos

- Terraform da Aula 4 aplicado (Function App provisionada, AI Services com custom subdomain, 3 roles concedidas).
- Áudio no container `audios` do Storage da Aula 2 (ver guia da Aula 4, Atividade 2).
- Reviews populadas no Cosmos da Aula 2 (ver Atividade 3 da Aula 2).
- Imagem no container `imagens` do Storage da Aula 2 (ver guia da Aula 4, Atividade 4).

## Deploy

```bash
FUNC_NAME=$(cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform && terraform output -raw function_app_name)

cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/function
func azure functionapp publish "$FUNC_NAME" --python
```

Tempo: ~2-3 min (mais pacotes que a Aula 3 — Speech SDK e Vision SDK pesam).

## Testar

```bash
HOSTNAME=$(cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform && terraform output -raw function_app_hostname)

# Aguardar Managed Identity propagar
sleep 90

# Health
curl -s "$HOSTNAME/api/health" | python3 -m json.tool

# Transcrever áudio
curl -s "$HOSTNAME/api/transcrever?blob=bbc-trecho.mp3" | python3 -m json.tool

# Analisar reviews do Cosmos
curl -s -X POST "$HOSTNAME/api/analisar-reviews?limit=10" | python3 -m json.tool

# Analisar imagem
curl -s "$HOSTNAME/api/analisar-imagem?blob=cadeira-produto.jpg" | python3 -m json.tool
```

## Lição central

Olhe o código — não há **nenhuma chave, token ou connection string**. A Function:

- Lê Blob via `DefaultAzureCredential` (role Storage Blob Data Reader).
- Chama AI Services via token AAD obtido pela MI (role Cognitive Services User + custom subdomain habilitado).
- Lê/escreve no Cosmos via MI (role Cosmos DB Built-in Data Contributor).

Este é o padrão de produção para componentes consumidos por agentes: **nenhum segredo no código, nenhum vazamento possível via repo**.
