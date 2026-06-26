# Function App Python 3.11 com Managed Identity SystemAssigned.
#
# >>> SUBSTITUI o function.tf do lab (aulas/03-serverless-containers/lab/terraform).
# A ÚNICA mudança em relação ao lab é a linha marcada com [N2.2]:
# conectar o Application Insights via connection string (Exercício 2.2).
# A segunda tool (calcular_frete, Exercício 2.1) NÃO precisa de mudança no
# Terraform — é só uma rota nova no MESMO Function App e no MESMO deploy.
resource "azurerm_linux_function_app" "fn" {
  name                       = "func-qc-${random_string.sufixo.result}"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  service_plan_id            = azurerm_service_plan.plan.id
  storage_account_name       = azurerm_storage_account.func_sa.name
  storage_account_access_key = azurerm_storage_account.func_sa.primary_access_key

  site_config {
    application_stack {
      python_version = "3.11"
    }

    # [N2.2] Observabilidade: liga o App Insights criado em appinsights.tf.
    # O provider injeta APPLICATIONINSIGHTS_CONNECTION_STRING automaticamente —
    # sem chave no código, a instrumentação é via runtime do Functions.
    application_insights_connection_string = azurerm_application_insights.fn.connection_string
  }

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "AzureWebJobsFeatureFlags" = "EnableWorkerIndexing"
    "STORAGE_ACCOUNT_AULA2"    = var.storage_account_aula2
  }

  tags = local.tags
}

# Permissão para a Managed Identity da Function ler blobs do Storage da Aula 2.
# É o que permite a Function operar sem credenciais no código (rota /produtos).
resource "azurerm_role_assignment" "fn_blob_reader" {
  scope                = data.azurerm_storage_account.aula2.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_linux_function_app.fn.identity[0].principal_id
}
