# =============================================================================
# Exercício 3.2 (N3 bônus) — Synapse Serverless SQL Pool sobre Blob da QC
# -----------------------------------------------------------------------------
# Objetivo: queryar os logs de compras (Parquet/CSV no Blob) DIRETO, sem ETL e
# sem carregar num DWH. O motor é o "Built-in" Serverless SQL Pool, que vem de
# graça com todo Synapse Workspace e cobra por TB *processado* na query.
#
# Pré-requisitos deste arquivo (já existem no lab da Aula 2):
#   - resource "azurerm_resource_group" "rg"   (main.tf)
#   - resource "azurerm_storage_account" "qc"  (storage.tf)
#   - resource "random_string" "sufixo"        (main.tf)
#   - variable "sql_admin_password" (sensitive) (variables.tf)  <-- reutilizada
#
# Senha do admin: NUNCA hardcoded. Passamos var.sql_admin_password, a mesma
# sensitive var já usada pelo Azure SQL. Para um deploy real:
#   export TF_VAR_sql_admin_password="$(openssl rand -base64 24)"
#   terraform apply
# =============================================================================

# -----------------------------------------------------------------------------
# 0) (Opcional) Se for declarar a variável aqui em vez de reaproveitar a de
#    variables.tf, descomente o bloco abaixo. NÃO mantenha as duas declarações.
#
# variable "sql_admin_password" {
#   description = "Senha do admin SQL do Synapse Workspace. Gere com: openssl rand -base64 24"
#   type        = string
#   sensitive   = true
# }
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 1) Data Lake Gen2 filesystem sobre a Storage Account da QC
# -----------------------------------------------------------------------------
# IMPORTANTE — TRADE-OFF DO HNS (Hierarchical Namespace / is_hns_enabled = true):
#
# Synapse exige que a conta de storage primária do workspace tenha HNS ligado
# (ADLS Gen2). O HNS troca o "flat namespace" de Blob por uma árvore real de
# diretórios. Consequências (FinOps + arquitetura):
#
#   PRÓS:
#     - Operações de diretório (rename/move/delete de pasta) são atômicas e O(1),
#       em vez de copiar+apagar objeto a objeto. Crítico para particionamento
#       (ex.: logs/ano=2026/mes=01/) e para partition pruning do Serverless.
#     - POSIX ACLs por diretório/arquivo -> governança fina sobre clickstream/logs.
#     - É o layout esperado por Synapse/Databricks/Spark (compute desacoplado).
#
#   CONTRAS:
#     - HNS NÃO pode ser ligado depois: é decidido na criação da conta. A conta
#       'stqc...' da Aula 2 foi criada SEM HNS (flat). Logo, NÃO dá para "ligar"
#       a flag nela; o Synapse usa um filesystem próprio nesta mesma conta SE ela
#       já for HNS, ou exige uma conta dedicada com HNS. Em produção a QC deve
#       criar a conta de analytics já com is_hns_enabled = true desde o dia 1.
#     - Operações por-blob (lifecycle/algumas APIs antigas) e certas features de
#       object storage têm pegada/custo levemente diferentes em conta HNS.
#     - Custo de transação e metadados ligeiramente maior que conta flat pura.
#
# Para o lab no Cloud Shell, o caminho honesto é provisionar UMA conta dedicada
# de analytics com HNS (abaixo), mantendo a 'stqc...' transacional intocada.
# Isso reflete a separação real: storage transacional vs. data lake analítico.
resource "azurerm_storage_account" "lake" {
  name                     = "stqclake${random_string.sufixo.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true # <-- HNS / ADLS Gen2 (obrigatório p/ Synapse). Vide trade-off acima.
  min_tls_version          = "TLS1_2"
  tags                     = local.tags
}

# Filesystem (container ADLS Gen2) que ancora o Synapse Workspace.
resource "azurerm_storage_data_lake_gen2_filesystem" "synapse" {
  name               = "synapsefs"
  storage_account_id = azurerm_storage_account.lake.id
}

# Filesystem onde ficam os logs de compras consultados pelo Serverless.
# Estrutura recomendada para partition pruning: compras/ano=YYYY/mes=MM/arquivo
resource "azurerm_storage_data_lake_gen2_filesystem" "logs" {
  name               = "logs"
  storage_account_id = azurerm_storage_account.lake.id
}

# -----------------------------------------------------------------------------
# 2) Synapse Workspace (traz o Serverless "Built-in" SQL pool de graça)
# -----------------------------------------------------------------------------
resource "azurerm_synapse_workspace" "qc" {
  name                                 = "syn-qc-${random_string.sufixo.result}"
  resource_group_name                  = azurerm_resource_group.rg.name
  location                             = azurerm_resource_group.rg.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.synapse.id

  # Admin SQL do workspace. Senha SEMPRE via variável sensitive (nunca hardcoded).
  sql_administrator_login          = "sqladminqc"
  sql_administrator_login_password = var.sql_admin_password

  # Identidade gerenciada: usada para o Serverless ler o Blob/Lake via RBAC
  # (Storage Blob Data Reader), em vez de chaves de conta.
  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# -----------------------------------------------------------------------------
# 3) Firewall do Synapse
# -----------------------------------------------------------------------------
# Permite que serviços Azure (o próprio Serverless engine) acessem o workspace.
resource "azurerm_synapse_firewall_rule" "allow_azure" {
  name                 = "AllowAllWindowsAzureIps"
  synapse_workspace_id = azurerm_synapse_workspace.qc.id
  start_ip_address     = "0.0.0.0"
  end_ip_address       = "0.0.0.0"
}

# Libera o IP atual do Cloud Shell (para abrir o Synapse Studio / sqlcmd daqui).
# Reaproveita o data source 'http.meu_ip' já definido em sql.tf.
resource "azurerm_synapse_firewall_rule" "cloud_shell" {
  name                 = "CloudShellAccess"
  synapse_workspace_id = azurerm_synapse_workspace.qc.id
  start_ip_address     = chomp(data.http.meu_ip.response_body)
  end_ip_address       = chomp(data.http.meu_ip.response_body)
}

# -----------------------------------------------------------------------------
# 4) RBAC: dá ao Serverless permissão de LER o Lake (sem chave de conta)
# -----------------------------------------------------------------------------
# A managed identity do workspace precisa de "Storage Blob Data Reader" no Lake
# para o OPENROWSET(BULK ...) com autenticação por identidade (Managed Identity).
resource "azurerm_role_assignment" "synapse_lake_reader" {
  scope                = azurerm_storage_account.lake.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_synapse_workspace.qc.identity[0].principal_id
}

# -----------------------------------------------------------------------------
# 5) Outputs úteis para a query e o upload dos CSVs
# -----------------------------------------------------------------------------
output "synapse_serverless_endpoint" {
  description = "Endpoint do Serverless SQL pool (use no Synapse Studio / sqlcmd)"
  value       = azurerm_synapse_workspace.qc.connectivity_endpoints["sqlOnDemand"]
}

output "lake_logs_url" {
  description = "Base URL do filesystem de logs para o OPENROWSET(BULK ...)"
  value       = "https://${azurerm_storage_account.lake.name}.dfs.core.windows.net/logs/"
}

output "lake_account_name" {
  description = "Nome da conta ADLS Gen2 (HNS) — destino do upload dos CSVs"
  value       = azurerm_storage_account.lake.name
}
