# Azure AI Services multi-service:
# 1 endpoint + 1 conjunto de chaves para Speech, Language, Vision, Document Intelligence, etc.
resource "azurerm_cognitive_account" "ai" {
  name                = "ai-qc-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  kind                = "CognitiveServices"
  sku_name            = "S0"

  # CRÍTICO para usar Managed Identity:
  # AI Services exige um custom subdomain para validar tokens AAD.
  custom_subdomain_name = "ai-qc-${random_string.sufixo.result}"

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}
