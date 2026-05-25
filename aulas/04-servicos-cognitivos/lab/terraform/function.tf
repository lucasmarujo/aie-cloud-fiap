# Function App Python 3.11 com Managed Identity SystemAssigned
resource "azurerm_linux_function_app" "fn" {
  name                       = "func-qc-aula04-${random_string.sufixo.result}"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  service_plan_id            = azurerm_service_plan.plan.id
  storage_account_name       = azurerm_storage_account.func_sa.name
  storage_account_access_key = azurerm_storage_account.func_sa.primary_access_key

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "AzureWebJobsFeatureFlags" = "EnableWorkerIndexing"
    "AI_ENDPOINT"              = azurerm_cognitive_account.ai.endpoint
    "STORAGE_ACCOUNT_AULA2"    = var.storage_account_aula2
    "COSMOS_ACCOUNT_AULA2"     = var.cosmos_account_aula2
  }

  tags = local.tags
}

# Role: Function pode chamar AI Services via Managed Identity (sem chave no código)
resource "azurerm_role_assignment" "fn_ai_user" {
  scope                = azurerm_cognitive_account.ai.id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_linux_function_app.fn.identity[0].principal_id
}

# Role: Function pode ler Blob da Aula 2 (áudios e imagens)
resource "azurerm_role_assignment" "fn_blob_reader" {
  scope                = data.azurerm_storage_account.aula2.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_linux_function_app.fn.identity[0].principal_id
}

# Cosmos role assignment (data plane) — ler reviews e fazer upsert
# Built-in role 00000000-0000-0000-0000-000000000002 = Cosmos DB Built-in Data Contributor
resource "azurerm_cosmosdb_sql_role_assignment" "fn_cosmos" {
  resource_group_name = var.resource_group_aula2
  account_name        = var.cosmos_account_aula2
  role_definition_id  = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${var.resource_group_aula2}/providers/Microsoft.DocumentDB/databaseAccounts/${var.cosmos_account_aula2}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = azurerm_linux_function_app.fn.identity[0].principal_id
  scope               = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${var.resource_group_aula2}/providers/Microsoft.DocumentDB/databaseAccounts/${var.cosmos_account_aula2}"
}
