variable "location" {
  description = "Região do Azure onde os recursos serão provisionados"
  type        = string
  default     = "brazilsouth"
}

variable "storage_account_aula2" {
  description = "Nome do Storage Account da Aula 2 (com produtos.csv, áudios e imagens). Pegue com: cd ../../02-storage-bancos/lab/terraform && terraform output -raw storage_account_name"
  type        = string
}

variable "resource_group_aula2" {
  description = "Nome do Resource Group da Aula 2"
  type        = string
}

variable "cosmos_account_aula2" {
  description = "Nome da conta Cosmos DB da Aula 2 (com reviews populadas). Pegue com: terraform output -raw cosmos_account_name (na pasta da Aula 2)"
  type        = string
}
