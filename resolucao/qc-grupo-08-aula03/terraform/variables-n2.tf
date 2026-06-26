# Variáveis novas da N2 (somam-se às do lab: location, storage_account_aula2,
# resource_group_aula2, aci_enabled).

variable "container_app_enabled" {
  description = "Quando true, provisiona o Azure Container App (Exercício 2.3). Deixe false no primeiro apply — a imagem produtos-api:v1 precisa existir no ACR antes (mesmo padrão do aci_enabled)."
  type        = bool
  default     = false
}
