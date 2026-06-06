# README — Nível 3 (IaC) · Pessoa C

Como rodar o que está nesta pasta. Tudo no **Azure Cloud Shell** — política "no install".

> ⚠️ **Custo:** a VM é `Standard_D2s_v3` + disco `Premium_LRS` (fora do free-tier, ~US$ 0,10/h). Sempre rode o `destroy`/`delete` ao final. Regra de ouro: custo zero quando não estiver usando.

Conteúdo:

```
pessoa-c/
├── terraform/      # Exercício 3.1 — VM + rede com SSH endurecido
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
└── bicep/          # Exercício 3.2 — mesma infra em Bicep
    └── main.bicep
```

---

## Pré-requisito — chave SSH no Cloud Shell

A VM autentica só por chave (sem senha). Garanta um par de chaves:

```bash
test -f ~/.ssh/id_rsa.pub || ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
```

---

## Exercício 3.1 — Terraform (SSH travado no seu IP)

```bash
cd terraform

# 1) Descubra seu IP público e crie o terraform.tfvars
cp terraform.tfvars.example terraform.tfvars
MEU_IP=$(curl -s ifconfig.me)
sed -i "s/203.0.113.45/$MEU_IP/" terraform.tfvars
echo "Seu IP: $MEU_IP"

# 2) Fluxo padrão
terraform init
terraform plan      # confira o diff (ver abaixo o que deve mudar)
terraform apply      # digite 'yes'

# 3) Conferir os outputs (IP público e de onde o SSH está liberado)
terraform output public_ip_address
terraform output ssh_allowed_from     # deve ser SEU_IP/32, nunca *

# 4) Limpeza OBRIGATÓRIA ao final
terraform destroy    # digite 'yes'
```

> Alternativa sem tfvars: `terraform apply -var "meu_ip=$(curl -s ifconfig.me)"`.

### O que o `terraform plan` deve mostrar (item 4 do enunciado)

Partindo do código original do lab (SSH com `source_address_prefix = "*"`), o plano da versão endurecida deve trazer **somente**:

| Símbolo | Recurso | Mudança |
|---------|---------|---------|
| `~` (update in-place) | `azurerm_network_security_group.nsg` | regra `SSH`: `source_address_prefix` muda de `"*"` para `"SEU_IP/32"` |
| `+` (create) | `azurerm_subnet.app` | nova subnet `subnet-app` (`10.0.2.0/24`) |

**A VM NÃO é recriada** (`azurerm_linux_virtual_machine.vm` não aparece no diff). Mudar uma regra de NSG e adicionar uma subnet são operações de rede — não tocam no ciclo de vida da VM. É exatamente o que o item 4 pede para demonstrar.

---

## Exercício 3.2 — Bicep (mesma infra)

Bicep precisa do Resource Group já existente (deploy em escopo de RG):

```bash
cd ../bicep

# 1) RG dedicado para o Bicep (separado do Terraform)
az group create --name rg-bicep-aula01 --location eastus2

# 2) Deploy — passa a chave SSH e o seu IP como parâmetros
az deployment group create \
  --resource-group rg-bicep-aula01 \
  --template-file main.bicep \
  --parameters adminPublicKey="$(cat ~/.ssh/id_rsa.pub)" meuIp="$(curl -s ifconfig.me)"

# 3) (opcional) Gerar o ARM JSON para a comparação de linhas do enunciado
bicep build main.bicep --outfile main.json
wc -l main.json     # use este número na tabela de comparação

# 4) Limpeza OBRIGATÓRIA ao final
az group delete --name rg-bicep-aula01 --yes --no-wait
```

> `main.json` é um artefato gerado — **não** precisa ir no ZIP da entrega.

---

## Checklist de limpeza (não deixar nada ligado)

```bash
# Terraform
cd terraform && terraform destroy -auto-approve

# Bicep
az group delete --name rg-bicep-aula01 --yes --no-wait

# Conferir que não sobrou nada gerando custo
az group list -o table
```
