# Guia de Laboratório — Aula 3

**Tema:** Serverless & Containers
**Plataforma:** Microsoft Azure (Azure for Students)
**Ambiente:** **Azure Cloud Shell** — tudo no browser, sem instalar nada

---

## Visão geral do lab

```
Atividade 1 — Function HTTP via Terraform + deploy com 'func'        ~30 min  (L₁)
Atividade 2 — Function lendo Blob (CSV QC) via Managed Identity      ~45 min  (L₂)
Atividade 3 — Mesmo código em container: Dockerfile + ACR + ACI      ~50 min  (L₃)
Wrap-up    — terraform destroy + verificação custo zero              ~10 min
```

> **Regra de ouro:** sempre encerrar com `terraform destroy`. Custo zero ao final.

---

## Pré-requisitos

- ✅ Aulas 1 e 2 concluídas (Cloud Shell funcional, Terraform rodando)
- ✅ **Storage da Aula 2 aplicado** com `produtos.csv` no container `catalogo`
- ✅ Repositório `aie-cloud` clonado no Cloud Shell

Se você destruiu o Storage da Aula 2, re-aplique antes:

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
SQL_PASSWORD=$(openssl rand -base64 24)
terraform apply -auto-approve -var="sql_admin_password=$SQL_PASSWORD"

# Re-upload do CSV (caso o container catalogo esteja vazio)
STORAGE=$(terraform output -raw storage_account_name)
az storage blob upload \
  --account-name "$STORAGE" --container-name catalogo \
  --name produtos.csv \
  --file ~/aie-cloud/aulas/02-storage-bancos/lab/data/produtos.csv \
  --auth-mode login --overwrite
```

---

## Preparação (5 min)

### Pegar os outputs da Aula 2

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
export STORAGE_AULA2=$(terraform output -raw storage_account_name)
export RG_AULA2=$(terraform output -raw resource_group_name)

echo "Storage da Aula 2: $STORAGE_AULA2"
echo "RG da Aula 2:      $RG_AULA2"
```

### Confirmar ferramentas no Cloud Shell

```bash
az account show --query "{nome:name, id:id}" -o table
terraform -version
func --version
docker --version
```

Se algum não responder, ver [Troubleshooting](#troubleshooting--problemas-comuns).

### Ir para o Terraform da Aula 3

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform
ls
# main.tf  variables.tf  outputs.tf  function.tf  containers.tf  README.md
```

Leia rapidamente cada `.tf` (3 min) — veja o [README do Terraform](terraform/README.md) para um resumo.

---

## Atividade 1 — Function HTTP via Terraform + deploy

**Objetivo:** Provisionar uma Azure Function App (Consumption Plan Y1 — grátis até 1M execuções/mês) e fazer deploy de uma função HTTP simples em Python (versão mock).

### Passo 1 — Phase 1 do Terraform

Provisiona Function App + ACR + identidades + roles. **Não cria o ACI ainda** (a imagem precisa existir primeiro).

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform

terraform init

terraform apply -auto-approve \
  -var="storage_account_aula2=$STORAGE_AULA2" \
  -var="resource_group_aula2=$RG_AULA2"
# aci_enabled=false (default) → ACI não é criado
```

Tempo: ~3-5 min. Anote os outputs (`function_app_name`, `acr_login_server`).

### Passo 2 — Deploy da versão mock (v1)

A pasta [function/v1-mock/](function/v1-mock/) tem código self-contained (5 produtos hardcoded — bom para validar que o pipeline de deploy funciona).

```bash
# Pegar o nome da Function App
FUNC_NAME=$(terraform output -raw function_app_name)
echo "Deploying em: $FUNC_NAME"

cd ~/aie-cloud/aulas/03-serverless-containers/lab/function/v1-mock
func azure functionapp publish "$FUNC_NAME" --python
```

Tempo: ~1-2 min. O `func` empacota o código e envia para o Azure.

### Passo 3 — Testar

```bash
HOSTNAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw function_app_default_hostname)

curl -s "$HOSTNAME/api/health" | python3 -m json.tool
curl -s "$HOSTNAME/api/produtos" | python3 -m json.tool
curl -s "$HOSTNAME/api/produtos?categoria=eletronicos" | python3 -m json.tool
curl -s "$HOSTNAME/api/produtos?nome=cadeira" | python3 -m json.tool
```

> **Primeira chamada vai demorar 2-3s** — cold start. Chamadas seguintes são milissegundos.

**✅ Checkpoint L₁:** O `curl` retorna JSON com lista de produtos mock?

---

## Atividade 2 — Function lendo Blob via Managed Identity

**Objetivo:** Trocar o mock por dados reais do Blob da Aula 2. **Sem credenciais no código** — autenticação via Managed Identity SystemAssigned (já criada no Passo 1).

### Conferir o que já foi provisionado

Abra [function.tf](terraform/function.tf) e observe:

- **`identity { type = "SystemAssigned" }`** no Function App — Azure cria automaticamente uma identidade gerenciada
- **`app_settings.STORAGE_ACCOUNT_AULA2`** — variável de ambiente já injetada (vem da var Terraform)
- **`azurerm_role_assignment.fn_blob_reader`** — concede `Storage Blob Data Reader` à Managed Identity no Storage da Aula 2

> **Tudo isso já foi aplicado no Passo 1 da Atividade 1.** Não há novo `terraform apply` aqui — só novo deploy de código.

### Passo 1 — Deploy da versão v2-blob

A pasta [function/v2-blob/](function/v2-blob/) tem o código que **lê o Blob via `DefaultAzureCredential`** — sem chaves no código.

```bash
FUNC_NAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw function_app_name)

cd ~/aie-cloud/aulas/03-serverless-containers/lab/function/v2-blob
func azure functionapp publish "$FUNC_NAME" --python
```

### Passo 2 — Testar

```bash
HOSTNAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw function_app_default_hostname)

# Agora retorna os 20 produtos REAIS do Blob!
curl -s "$HOSTNAME/api/produtos?categoria=moveis" | python3 -m json.tool
curl -s "$HOSTNAME/api/produtos?nome=cadeira" | python3 -m json.tool
```

> **Erro comum:** "AuthorizationFailure" — a role demorou para propagar. Aguarde 1-2 min e tente novamente.

### Passo 3 — Reflexão (3 min)

Anote no `entrega-grupo-aula03.md` do seu grupo:

1. Procure por "key", "password", "credential", "secret" em todo o código da Function v2-blob. O que você encontra?
2. Como a Function consegue ler o Blob "sem credenciais"?
3. Se um agente em produção precisar acessar 5 storage accounts diferentes, qual a estratégia recomendada?

**✅ Checkpoint L₂:** A Function retorna os 20 produtos reais do CSV?

---

## Atividade 3 — Containerização + ACR + ACI

**Objetivo:** Pegar o **mesmo código** (em FastAPI) e empacotá-lo num container Docker. Publicar no ACR e rodar no ACI com Managed Identity user-assigned.

### Conferir o código FastAPI

[docker/app.py](docker/app.py) tem a mesma lógica da Function v2-blob (lê Blob via MI), mas usando FastAPI. O [Dockerfile](docker/Dockerfile) usa **multi-stage build** para imagem leve (~150 MB).

### Passo 1 — Build da imagem via ACR Tasks (recomendado)

Usa o servidor do ACR para fazer o build — **não consome quota** do Cloud Shell:

```bash
ACR_NAME=$(cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform && terraform output -raw acr_name)

cd ~/aie-cloud/aulas/03-serverless-containers/lab/docker
az acr build -t produtos-api:v1 -r "$ACR_NAME" .

# Confirmar
az acr repository list -n "$ACR_NAME" -o table
```

### Passo 1 (alternativa) — Build local no Cloud Shell

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/docker
docker build -t produtos-api:v1 .

# Teste local opcional (vai falhar em /produtos — Cloud Shell não tem MI no container)
docker run --rm -p 8080:8080 \
  -e STORAGE_ACCOUNT_AULA2="$STORAGE_AULA2" \
  produtos-api:v1 &
sleep 3
curl http://localhost:8080/health   # funciona
curl 'http://localhost:8080/produtos?categoria=moveis'  # falha (sem MI local)
docker stop $(docker ps -lq)

# Push para o ACR
ACR=$(cd ../terraform && terraform output -raw acr_login_server)
ACR_NAME=$(cd ../terraform && terraform output -raw acr_name)
az acr login -n "$ACR_NAME"

docker tag produtos-api:v1 "$ACR/produtos-api:v1"
docker push "$ACR/produtos-api:v1"
```

### Passo 2 — Phase 2 do Terraform (habilitar ACI)

Com a imagem no ACR, agora habilita o ACI:

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform

terraform apply -auto-approve \
  -var="storage_account_aula2=$STORAGE_AULA2" \
  -var="resource_group_aula2=$RG_AULA2" \
  -var="aci_enabled=true"
```

Tempo: ~1 min. O ACI puxa a imagem do ACR e sobe o container.

### Passo 3 — Testar o ACI

```bash
ACI_FQDN=$(terraform output -raw aci_fqdn)
echo "ACI: $ACI_FQDN"

# Aguardar Managed Identity propagar
sleep 60

curl "http://$ACI_FQDN:8080/health"
curl "http://$ACI_FQDN:8080/produtos?categoria=moveis"
```

### Passo 4 — Comparação Function vs ACI (5 min)

| Aspecto | Function | ACI |
|---------|----------|-----|
| URL | `https://<func>.azurewebsites.net/api/produtos` | `http://<aci>:8080/produtos` |
| TLS | ✅ Built-in | ❌ Não (manual com Front Door/AppGw) |
| Cold start | 1-3s | Não há (container sempre on) |
| Custo idle | $0 | $$ pay-per-second mesmo idle |
| Auto-scale | ✅ 0-200 | ❌ 1 réplica fixa |
| Linguagem | Python/.NET/JS/Java | Qualquer |
| Identidade | System-assigned MI | User-assigned MI |

**Pergunta para o `entrega-grupo-aula03.md`:**

Para a QC, qual você levaria para produção da API de catálogo? Justifique em 3-5 frases considerando: tráfego esperado, custo, latência aceitável, complexidade operacional.

**✅ Checkpoint L₃:** Você fez deploy do mesmo código em 2 formas (Function + ACI) e ambos respondem `/produtos`?

---

## Wrap-up — Destroy e custo zero (10 min)

### Passo 1 — Destruir o ambiente da Aula 3

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform

terraform destroy -auto-approve \
  -var="storage_account_aula2=$STORAGE_AULA2" \
  -var="resource_group_aula2=$RG_AULA2" \
  -var="aci_enabled=true"
```

Tempo: ~2 min. O Storage da Aula 2 NÃO é destruído (é `data` source).

### Passo 2 — Decidir sobre a Aula 2

Opções:

1. **Manter Aula 2 aplicada** — útil para exercícios de container/agente que reusem os dados
2. **Destruir Aula 2 também** — re-aplicar antes da Aula 4

```bash
# Opção 2: destruir Aula 2 também (recomendado para custo zero garantido)
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
terraform destroy -auto-approve -var="sql_admin_password=qualquer"
```

### Passo 3 — Verificar custo

Portal → **Cost Management** → **Análise de Custo** → filtrar por hoje. Total deve estar < $1.

---

## Conexão com o projeto Quantum Commerce

**Saída desta aula:**

- Function App + ACR + ACI provisionados via Terraform
- API de catálogo da QC funcionando em **2 sabores** — você decide qual leva para o projeto integrado final

**Para os agentes da QC (Aula 4 e disciplinas seguintes do MBA):**

A API que você implantou é a primeira **tool** que os agentes da QC vão consumir. Spec sugerida:

```json
{
  "name": "buscar_produtos_qc",
  "description": "Busca produtos da Quantum Commerce por categoria ou nome",
  "input_schema": {
    "type": "object",
    "properties": {
      "categoria": {"type": "string", "description": "Categoria (ex: moveis, eletronicos)"},
      "nome":      {"type": "string", "description": "Substring do nome do produto"}
    }
  }
}
```

Na Aula 4 vamos adicionar mais tools (busca por imagem com Vision, transcrição com Speech, etc.).

---

## Troubleshooting — Problemas comuns

| Problema | Causa | Solução |
|----------|-------|---------|
| `func: command not found` | Functionalidade não habilitada no Cloud Shell | Executar `npm install -g azure-functions-core-tools@4 --unsafe-perm true` (geralmente já vem por padrão) |
| `func azure functionapp publish` retorna 401 | Cloud Shell não autenticado | `az login` ou `az account set --subscription <id>` |
| Function retorna 403 "AuthorizationFailed" | MI ainda propagando | Aguardar 1-2 min |
| Function retorna 500 "STORAGE_ACCOUNT_AULA2 not set" | Variável de ambiente não chegou | Verificar `app_settings` no TF + `terraform apply` de novo |
| `docker build` "no space left on device" | Quota do Cloud Shell esgotada | Usar `az acr build` (build server-side) |
| ACI fica em "Pulling image" eternamente | Credencial do ACR errada | Verificar `image_registry_credential` no TF; testar `docker pull <acr>/produtos-api:v1` |
| ACI "Crashed" | App levantou e morreu | `az container logs -n <aci-name> -g <rg>` para ver erro |
| ACI retorna timeout no `curl` | DNS ainda propagando | Aguardar 30s |
| FastAPI roda local mas falha no ACI | MI não propagou para subscription | Aguardar 1-2 min e tentar de novo |

---

## Referências

- [Azure Functions Python — programming model v2](https://learn.microsoft.com/azure/azure-functions/functions-reference-python?pivots=python-mode-decorators)
- [Azure Functions Core Tools (`func`)](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [DefaultAzureCredential — chain de autenticação](https://learn.microsoft.com/python/api/overview/azure/identity-readme#defaultazurecredential)
- [Managed Identity overview](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview)
- [Azure Container Registry — quickstart](https://learn.microsoft.com/azure/container-registry/container-registry-get-started-azure-cli)
- [Azure Container Instances overview](https://learn.microsoft.com/azure/container-instances/container-instances-overview)
- [Container Apps vs ACI vs Functions](https://learn.microsoft.com/azure/container-apps/compare-options)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Terraform AzureRM Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
