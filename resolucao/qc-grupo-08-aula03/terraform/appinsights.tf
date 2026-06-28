# ---------------------------------------------------------------------------
# Exercício 2.2 — Application Insights + Log Analytics (observabilidade)
#
# A Aula 3 desabilitou o App Insights por custo. Aqui reabilitamos no modelo
# atual (workspace-based Application Insights; o "classic" foi aposentado pela
# Microsoft). O MESMO Log Analytics workspace serve também o Container App
# (2.3) — uma única tela (single pane of glass) para logs/métricas/traces.
# Arquivo NOVO: some-se aos .tf do lab.
# ---------------------------------------------------------------------------

resource "azurerm_log_analytics_workspace" "qc" {
  name                = "log-qc-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "PerGB2018"
  retention_in_days   = 30 # custo controlado; produção ajustaria por compliance
  tags                = local.tags
}

resource "azurerm_application_insights" "fn" {
  name                = "appi-qc-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  workspace_id        = azurerm_log_analytics_workspace.qc.id
  application_type    = "web"
  tags                = local.tags
}
