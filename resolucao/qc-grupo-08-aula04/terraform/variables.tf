variable "resource_group_name" {
  description = "Nome do Resource Group da Aula 4. Obter com: terraform output -raw resource_group_name"
  type        = string
}

variable "function_app_name" {
  description = "Nome da Function App da Aula 4. Obter com: terraform output -raw function_app_name"
  type        = string
}

variable "openai_location" {
  description = "Região do Azure OpenAI (eastus2 ou swedencentral — Brazil South não tem OpenAI)"
  type        = string
  default     = "eastus2"
}
