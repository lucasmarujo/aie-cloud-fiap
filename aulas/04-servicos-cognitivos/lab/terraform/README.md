# Terraform — Aula 4

Código IaC para provisionar a **camada cognitiva** da Quantum Commerce:

- **Azure AI Services multi-service (S0)** — 1 endpoint para Speech, Language e Vision, com `custom_subdomain_name` habilitado (pré-requisito para Managed Identity).
- **Key Vault** com a chave do AI Services como segredo (didático).
- **Function App** Python 3.11 (Consumption Y1) com Managed Identity SystemAssigned.
- **Roles** na Function: `Cognitive Services User` no AI Services + `Storage Blob Data Reader` na Aula 2 + `Cosmos DB Built-in Data Contributor` no Cosmos da Aula 2.

## Pré-requisito

O Storage e o Cosmos da Aula 2 precisam estar aplicados (com `produtos.csv` no Blob e reviews populadas no Cosmos). Pegue os valores antes:

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
export STORAGE_AULA2=$(terraform output -raw storage_account_name)
export RG_AULA2=$(terraform output -raw resource_group_name)
export COSMOS_AULA2=$(terraform output -raw cosmos_account_name)
echo "Storage: $STORAGE_AULA2 | RG: $RG_AULA2 | Cosmos: $COSMOS_AULA2"
```

## Como usar (no Azure Cloud Shell)

```bash
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform

terraform init

terraform apply -auto-approve \
  -var="storage_account_aula2=$STORAGE_AULA2" \
  -var="resource_group_aula2=$RG_AULA2" \
  -var="cosmos_account_aula2=$COSMOS_AULA2"
```

Tempo: ~3-5 min (AI Services demora um pouco).

## Destroy

```bash
terraform destroy -auto-approve \
  -var="storage_account_aula2=$STORAGE_AULA2" \
  -var="resource_group_aula2=$RG_AULA2" \
  -var="cosmos_account_aula2=$COSMOS_AULA2"
```

> Storage e Cosmos da Aula 2 NÃO são destruídos (são `data` source).

## Arquivos

| Arquivo | O que define |
|---------|--------------|
| [main.tf](main.tf) | Providers, RG, locals, storage da Function, plan Y1, data sources |
| [variables.tf](variables.tf) | `location` + 3 vars que apontam para recursos da Aula 2 |
| [outputs.tf](outputs.tf) | Nomes/endpoints consumidos pelo guia e pela Function |
| [cognitive.tf](cognitive.tf) | Azure AI Services multi-service (Speech, Language, Vision) |
| [keyvault.tf](keyvault.tf) | Key Vault + role + segredo `ai-services-key` |
| [function.tf](function.tf) | Function App + Managed Identity + 3 role assignments |

## Outputs disponíveis

```bash
terraform output -raw function_app_name
terraform output -raw function_app_hostname
terraform output -raw ai_endpoint
terraform output -raw key_vault_name
```

## Observações

- **Custom subdomain:** sem ele, a Managed Identity não consegue chamar o AI Services. Já está configurado em `cognitive.tf`.
- **Cosmos role data plane via Terraform:** ao contrário da Aula 3 (que usa `az cosmosdb sql role assignment` por CLI), aqui o role do Cosmos é declarado como `azurerm_cosmosdb_sql_role_assignment`.
- **Custo:** AI Services S0 é pay-per-call. Sem chamadas = sem custo. Function Consumption Y1 = grátis até 1M req/mês.
