# Outputs novos da N2 (somam-se aos do lab: function_app_name, acr_*, aci_fqdn...).

output "app_insights_name" {
  description = "Nome do Application Insights — abrir no portal -> Live Metrics / Failures (2.2)"
  value       = azurerm_application_insights.fn.name
}

output "log_analytics_workspace_name" {
  description = "Workspace Log Analytics compartilhado (Function + Container App)"
  value       = azurerm_log_analytics_workspace.qc.name
}

output "container_app_url" {
  description = "URL HTTPS do Container App quando habilitado (2.3)"
  value       = var.container_app_enabled ? "https://${azurerm_container_app.produtos[0].ingress[0].fqdn}" : "Container App nao habilitado — rode 'terraform apply' com -var container_app_enabled=true apos o push da imagem produtos-api:v1"
}
