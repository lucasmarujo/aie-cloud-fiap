output "resource_group_name" {
  description = "Nome do Resource Group criado"
  value       = azurerm_resource_group.rg.name
}

output "vm_name" {
  description = "Nome da máquina virtual"
  value       = azurerm_linux_virtual_machine.vm.name
}

# [3.1 — item 3] Output que expõe APENAS o IP público da VM.
# Já existia no lab; confirmamos que ele continua aparecendo após o apply.
output "public_ip_address" {
  description = "IP público da VM"
  value       = azurerm_public_ip.pip.ip_address
}

output "ssh_command" {
  description = "Comando pronto para conectar na VM (a partir do Cloud Shell)"
  value       = "ssh ${var.admin_username}@${azurerm_public_ip.pip.ip_address}"
}

output "admin_username" {
  description = "Usuário administrador da VM"
  value       = azurerm_linux_virtual_machine.vm.admin_username
}

# [3.1 — item 1] Output de verificação: mostra de qual origem o SSH está liberado.
# Útil para conferir, depois do apply, que a porta 22 NÃO está mais aberta para "*".
output "ssh_allowed_from" {
  description = "Origem (CIDR) autorizada a acessar o SSH — deve ser o seu IP /32, nunca *"
  value       = "${var.meu_ip}/32"
}

# [3.1 — item 2] Outputs das duas subnets, para evidenciar a separação de camadas.
output "subnets" {
  description = "Subnets da VNet: 'default' (gestão/SSH) e 'subnet-app' (futura camada de aplicação da QC)"
  value = {
    default = azurerm_subnet.default.address_prefixes[0]
    app     = azurerm_subnet.app.address_prefixes[0]
  }
}
