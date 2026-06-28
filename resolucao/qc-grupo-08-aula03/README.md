# Entrega Aula 03 — Grupo 08 — Nível 2 (como rodar)

Pacote da seção **🟡 N2** da Entrega 3 (Serverless & Containers): segunda tool
(cálculo de frete), Application Insights e migração para Container Apps.
Resposta completa em [`respostas-N2-aula03.md`](respostas-N2-aula03.md).

> **Política "no install":** tudo roda no **Azure Cloud Shell**. Os comandos
> abaixo assumem o repositório do grupo clonado e os outputs da Aula 2/Aula 3
> disponíveis (ver guia do lab da Aula 3).

## Estrutura

```
qc-grupo08-aula03/
├── respostas-N2-aula03.md        # documento principal (respostas 2.1, 2.2, 2.3)
├── README.md                     # este arquivo
├── function/                     # Function evoluída (produtos + frete + health)
│   ├── function_app.py           #   rotas HTTP (2.1.b)
│   ├── frete_calc.py             #   regra de frete PURA e determinística
│   ├── requirements.txt
│   ├── host.json
│   └── tests/test_frete_calc.py  #   17 testes, rodam offline
├── tools/                        # contrato das tools p/ o agente (JSON Schema)
│   ├── buscar_produtos_qc.tool.json
│   └── calcular_frete_qc.tool.json   # 2.1.d
├── terraform/                    # deltas N2 sobre o terraform do lab
│   ├── function.tf               #   SUBSTITUI o do lab (+1 linha de App Insights)
│   ├── appinsights.tf            #   2.2.a — AI + Log Analytics
│   ├── containerapps.tf          #   2.3 — Container App Environment + App
│   ├── variables-n2.tf           #   var container_app_enabled
│   └── outputs-n2.tf
├── scripts/
│   ├── calcular_frete_local.py   # exercita a regra de frete offline
│   └── gerar_carga.py            # 20 chamadas variadas p/ Live Metrics (2.2.b)
└── diagramas/
    └── README.md                 # onde colocar o print do Live Metrics
```

## 1. Validar a regra de frete (offline, sem Azure) — Exercício 2.1

```bash
cd function
python -m pip install --user pytest      # se necessário
python -m pytest -q                        # 17 testes
cd ..
python scripts/calcular_frete_local.py     # tabela de exemplos
python scripts/calcular_frete_local.py 01310-100 60160-230 3.2   # cálculo pontual
```

## 2. Deploy da Function com as 2 tools

A Function é a do lab evoluída — mesmo Function App, mesmo `func publish`.

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform
FUNC_NAME=$(terraform output -raw function_app_name)
HOST=$(terraform output -raw function_app_default_hostname)

# usa o código deste pacote (com frete_calc.py + calcular_frete)
cd <repo-do-grupo>/qc-grupo08-aula03/function
func azure functionapp publish "$FUNC_NAME" --python

curl "$HOST/api/health"
curl "$HOST/api/produtos?categoria=moveis"
curl "$HOST/api/calcular_frete?cep_origem=01310-100&cep_destino=20040-002&peso=2.5"
```

## 3. Application Insights — Exercício 2.2

Os arquivos `terraform/` deste pacote **estendem** o terraform do lab. Copie-os
para `aulas/03-serverless-containers/lab/terraform/` (o `function.tf` daqui
**substitui** o do lab — a única diferença é a linha que liga o App Insights),
e reaplique:

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform
terraform apply -auto-approve \
  -var="storage_account_aula2=$STORAGE_AULA2" \
  -var="resource_group_aula2=$RG_AULA2"

# redeploy do código para a Function já com App Insights ligado
cd <repo-do-grupo>/qc-grupo08-aula03/function
func azure functionapp publish "$FUNC_NAME" --python

# 20 chamadas variadas (16 ok + 4 falhas propositais) → abra Live Metrics durante
cd <repo-do-grupo>/qc-grupo08-aula03
python scripts/gerar_carga.py "$HOST"
```

Print do Live Metrics em `diagramas/` (ver `diagramas/README.md`).

## 4. Container Apps — Exercício 2.3

A imagem `produtos-api:v1` já existe no ACR (Atividade 3 do lab). Habilite o
Container App (mesmo padrão do `aci_enabled` — só após a imagem existir):

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform
terraform apply -auto-approve \
  -var="storage_account_aula2=$STORAGE_AULA2" \
  -var="resource_group_aula2=$RG_AULA2" \
  -var="container_app_enabled=true"

CA_URL=$(terraform output -raw container_app_url)
curl "$CA_URL/health"
curl "$CA_URL/produtos?categoria=moveis"
```

## 5. Limpeza (custo zero)

```bash
cd ~/aie-cloud/aulas/03-serverless-containers/lab/terraform
terraform destroy -auto-approve \
  -var="storage_account_aula2=$STORAGE_AULA2" \
  -var="resource_group_aula2=$RG_AULA2" \
  -var="container_app_enabled=true"
```

## Verificações já feitas neste pacote

- `python -m pytest -q` → **17 passed** (regra de frete).
- `scripts/gerar_carga.py` validado ponta-a-ponta contra mock local (16 ok + 4 falhas propositais).
- `terraform validate` (base do lab + deltas N2, provider azurerm ~3.100) → **Success! The configuration is valid.**
- `terraform fmt` aplicado.
