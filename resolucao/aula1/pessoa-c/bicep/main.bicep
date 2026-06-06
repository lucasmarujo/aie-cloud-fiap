// ---------------------------------------------------------------------------
// main.bicep — Equivalente Bicep da VM Linux do lab (Aula 1, Atividade 5)
// Mesma infra do main.tf endurecido (Exercício 3.1):
//   VNet 10.0.0.0/16 + subnet 'default' (10.0.0.0/24) + subnet 'subnet-app' (10.0.2.0/24)
//   + NSG (SSH travado no seu IP, HTTPS, HTTP) + IP público Standard + NIC + VM Ubuntu 24.04
//
// Escopo: Resource Group (o RG precisa existir ANTES — ver README).
// Deploy:
//   az group create -n rg-bicep-aula01 -l eastus2
//   az deployment group create -g rg-bicep-aula01 -f main.bicep \
//     -p adminPublicKey="$(cat ~/.ssh/id_rsa.pub)" meuIp="$(curl -s ifconfig.me)"
// ---------------------------------------------------------------------------

@description('Região dos recursos. Default = região do Resource Group.')
param location string = resourceGroup().location

@description('Usuário administrador da VM.')
param adminUsername string = 'azureuser'

@description('Conteúdo da chave pública SSH (~/.ssh/id_rsa.pub).')
@secure()
param adminPublicKey string

@description('Seu IPv4 público (curl ifconfig.me). SSH é liberado apenas para ele (/32).')
param meuIp string

@description('Tamanho da VM.')
param vmSize string = 'Standard_D2s_v3'

var tags = {
  aula: '1'
  disciplina: 'cloud-cognitive'
  provisionado: 'bicep'
}

resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: 'vm-lab-aula01-vnet'
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [ '10.0.0.0/16' ]
    }
    subnets: [
      {
        name: 'default'
        properties: {
          addressPrefix: '10.0.0.0/24'
        }
      }
      {
        // Segunda subnet: futura camada de aplicação da QC (paridade com o 3.1)
        name: 'subnet-app'
        properties: {
          addressPrefix: '10.0.2.0/24'
        }
      }
    ]
  }
}

resource nsg 'Microsoft.Network/networkSecurityGroups@2023-09-01' = {
  name: 'vm-lab-aula01-nsg'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        // SSH liberado APENAS para o seu IP (/32), não para '*'
        name: 'SSH'
        properties: {
          priority: 300
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '22'
          sourceAddressPrefix: '${meuIp}/32'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'HTTPS'
        properties: {
          priority: 320
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'HTTP'
        properties: {
          priority: 340
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '80'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

resource pip 'Microsoft.Network/publicIPAddresses@2023-09-01' = {
  name: 'vm-lab-aula01-ip'
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource nic 'Microsoft.Network/networkInterfaces@2023-09-01' = {
  name: 'vm-lab-aula01-nic'
  location: location
  tags: tags
  properties: {
    enableAcceleratedNetworking: true
    // No template ARM/Terraform o NSG é associado à NIC (não à subnet)
    networkSecurityGroup: {
      id: nsg.id
    }
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          subnet: {
            id: '${vnet.id}/subnets/default'
          }
          privateIPAllocationMethod: 'Dynamic'
          publicIPAddress: {
            id: pip.id
          }
        }
      }
    ]
  }
}

resource vm 'Microsoft.Compute/virtualMachines@2024-03-01' = {
  name: 'vm-lab-aula01'
  location: location
  tags: tags
  properties: {
    hardwareProfile: {
      vmSize: vmSize
    }
    osProfile: {
      computerName: 'vm-lab-aula01'
      adminUsername: adminUsername
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: {
          publicKeys: [
            {
              path: '/home/${adminUsername}/.ssh/authorized_keys'
              keyData: adminPublicKey
            }
          ]
        }
      }
    }
    storageProfile: {
      imageReference: {
        publisher: 'canonical'
        offer: 'ubuntu-24_04-lts'
        sku: 'server'
        version: 'latest'
      }
      osDisk: {
        caching: 'ReadWrite'
        createOption: 'FromImage'
        managedDisk: {
          storageAccountType: 'Premium_LRS'
        }
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: nic.id
        }
      ]
    }
    diagnosticsProfile: {
      bootDiagnostics: {
        enabled: true
      }
    }
  }
}

// Outputs equivalentes aos do Terraform
output publicIpAddress string = pip.properties.ipAddress
output sshAllowedFrom string = '${meuIp}/32'
output adminUsername string = adminUsername
