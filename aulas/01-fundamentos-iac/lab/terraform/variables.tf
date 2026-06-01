variable "location" {
  description = "Região do Azure onde os recursos serão provisionados (igual ao template: eastus2)"
  type        = string
  default     = "eastus2"
}

variable "resource_group_name" {
  description = "Resource Group da versão IaC da VM (separado do rg-lab-aula01 criado no portal)"
  type        = string
  default     = "rg-iac-aula01"
}

variable "vm_size" {
  description = "Tamanho da VM (igual ao template exportado do portal)"
  type        = string
  default     = "Standard_D2s_v3"
}

variable "admin_username" {
  description = "Usuário administrador da VM"
  type        = string
  default     = "azureuser"
}

variable "ssh_public_key_path" {
  description = "Caminho da chave pública SSH usada para acessar a VM (no Cloud Shell: ~/.ssh/id_rsa.pub)"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}
