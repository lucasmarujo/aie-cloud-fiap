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

# [3.1 — item 1] Seu IP público, usado para restringir o SSH (porta 22) a apenas você.
# Sem default de propósito: força informar via `terraform.tfvars` ou `-var`, evitando
# que alguém aplique sem perceber que está liberando o próprio IP. O `/32` é adicionado
# no main.tf (regra SSH do NSG). Obtenha com `curl -s ifconfig.me` no Cloud Shell.
variable "meu_ip" {
  description = "Seu IPv4 público (sem máscara). Ex.: 203.0.113.45. O /32 é aplicado automaticamente."
  type        = string

  validation {
    condition     = can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}$", var.meu_ip))
    error_message = "meu_ip deve ser um IPv4 sem máscara (ex.: 203.0.113.45). Não inclua /32 — ele é adicionado pelo código."
  }
}
