# ---------------------------------------------------------------------------
# Exercício 2.3 — Migrar a API de catálogo para Azure Container Apps
#
# Roda o MESMO container produtos-api:v1 do ACR (Atividade 3 do lab) num
# ambiente serverless de containers: scale-to-zero, HTTPS gerenciado no FQDN e
# autoscaling por requisições concorrentes.
#
# Auth no ACR e no Blob via Managed Identity user-assigned (sem admin user, sem
# chave) — coerente com o tema de segurança do projeto (Aula 2: MI > credencial).
# Arquivo NOVO: some-se aos .tf do lab (reusa acr, rg, data.aula2, workspace).
# ---------------------------------------------------------------------------

# Identidade gerenciada dedicada do Container App
resource "azurerm_user_assigned_identity" "aca_id" {
  name                = "id-aca-qc-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  tags                = local.tags
}

# Puxar a imagem do ACR sem admin user (AcrPull no registry da Atividade 3)
resource "azurerm_role_assignment" "aca_acrpull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.aca_id.principal_id
}

# Ler o produtos.csv do Blob da Aula 2 (mesma role da Function/ACI)
resource "azurerm_role_assignment" "aca_blob_reader" {
  scope                = data.azurerm_storage_account.aula2.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_user_assigned_identity.aca_id.principal_id
}

# Ambiente do Container Apps (reaproveita o Log Analytics do appinsights.tf)
resource "azurerm_container_app_environment" "qc" {
  name                       = "cae-qc-${random_string.sufixo.result}"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.qc.id
  tags                       = local.tags
}

# O Container App só sobe quando a imagem já existe no ACR (mesmo padrão do
# aci_enabled do lab). Primeiro apply: container_app_enabled=false.
resource "azurerm_container_app" "produtos" {
  count = var.container_app_enabled ? 1 : 0

  name                         = "ca-produtos-qc-${random_string.sufixo.result}"
  resource_group_name          = azurerm_resource_group.rg.name
  container_app_environment_id = azurerm_container_app_environment.qc.id
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aca_id.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.aca_id.id
  }

  ingress {
    external_enabled = true
    target_port      = 8080
    transport        = "auto" # TLS/HTTPS gerenciado no FQDN *.azurecontainerapps.io

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 0 # scale-to-zero -> custo idle = 0
    max_replicas = 10

    container {
      name   = "produtos-api"
      image  = "${azurerm_container_registry.acr.login_server}/produtos-api:v1"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "STORAGE_ACCOUNT_AULA2"
        value = var.storage_account_aula2
      }
      # Desambigua qual identidade o DefaultAzureCredential usa (há user-assigned)
      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.aca_id.client_id
      }
    }

    # Scale rule pedida: escalar quando passar de 50 requisições concorrentes
    http_scale_rule {
      name                = "http-concorrencia"
      concurrent_requests = "50"
    }
  }

  tags = local.tags

  depends_on = [azurerm_role_assignment.aca_acrpull]
}
