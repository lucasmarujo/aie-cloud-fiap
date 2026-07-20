# ─────────────────────────────────────────────────────────────────────────────
# N3 3.1 — Azure OpenAI com text-embedding-3-small e gpt-4o-mini
# Responsável: Pessoa 2 (Luciana) — embeddings + dependência do N3 3.3 (Lucas)
#
# ATENÇÃO: Azure OpenAI não está disponível em Brazil South.
# Usar eastus2 ou swedencentral.
# ─────────────────────────────────────────────────────────────────────────────

# ── Conta Azure OpenAI ────────────────────────────────────────────────────────
resource "azurerm_cognitive_account" "openai" {
  name                = "openai-qc-${random_string.sufixo.result}"
  location            = var.openai_location
  resource_group_name = data.azurerm_resource_group.rg.name
  kind                = "OpenAI"
  sku_name            = "S0"

  # custom_subdomain obrigatório para autenticação via Managed Identity (Ex. 1.3)
  custom_subdomain_name = "openai-qc-${random_string.sufixo.result}"
}

# ── Deployment: text-embedding-3-small (N3 3.1 — Pessoa 2) ───────────────────
resource "azurerm_cognitive_deployment" "embeddings" {
  name                 = "text-embedding-3-small"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-small"
    version = "1"
  }

  sku {
    name     = "Standard"
    capacity = 30
  }
}

# ── Deployment: gpt-4o-mini (N3 3.3 — Pessoa 3 / Lucas) ──────────────────────
resource "azurerm_cognitive_deployment" "chat" {
  name                 = "gpt-4o-mini"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o-mini"
    version = "2024-07-18"
  }

  sku {
    name     = "Standard"
    capacity = 20
  }

  depends_on = [azurerm_cognitive_deployment.embeddings]
}

# ── Role: Function MI pode chamar o Azure OpenAI sem chave ───────────────────
resource "azurerm_role_assignment" "fn_openai_user" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = data.azurerm_linux_function_app.fn.identity[0].principal_id
}

# Role para o usuário autenticado no Cloud Shell rodar o script N3 3.1
resource "azurerm_role_assignment" "shell_openai_user" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = data.azurerm_client_config.current.object_id
}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "openai_endpoint" {
  description = "Endpoint do Azure OpenAI — use como AZURE_OPENAI_ENDPOINT"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "openai_embedding_deployment" {
  value = azurerm_cognitive_deployment.embeddings.name
}

output "openai_chat_deployment" {
  value = azurerm_cognitive_deployment.chat.name
}
