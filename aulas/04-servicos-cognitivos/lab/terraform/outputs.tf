output "resource_group_name" {
  description = "Nome do Resource Group da Aula 4"
  value       = azurerm_resource_group.rg.name
}

# AI Services
output "ai_endpoint" {
  description = "Endpoint do Azure AI Services (Speech, Language, Vision)"
  value       = azurerm_cognitive_account.ai.endpoint
}

output "ai_name" {
  description = "Nome do recurso AI Services"
  value       = azurerm_cognitive_account.ai.name
}

# Key Vault
output "key_vault_name" {
  description = "Nome do Key Vault (com a chave do AI Services como segredo)"
  value       = azurerm_key_vault.kv.name
}

# Function
output "function_app_name" {
  description = "Nome da Function App"
  value       = azurerm_linux_function_app.fn.name
}

output "function_app_hostname" {
  description = "URL HTTPS da Function App"
  value       = "https://${azurerm_linux_function_app.fn.default_hostname}"
}
