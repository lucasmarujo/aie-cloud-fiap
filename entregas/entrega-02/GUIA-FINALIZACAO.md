# Guia de finalização — Entrega 2 (Aula 2) — Grupo 08

Passo a passo para **testar o N3 no Azure**, **substituir os números representativos pelos reais** e **gerar o ZIP** para o Portal FIAP. Tempo estimado: ~60–90 min (a maior parte é espera de `terraform apply`).

> ⚠️ **Por que testar?** As tabelas do N3 (scores, latências, bytes) hoje são *representativas* — foram montadas sem Azure provisionado. A rubrica dá **+2 pts** com "implementação correta **+ reflexão aprofundada**". Rodar de verdade e colar os números reais elimina qualquer ressalva.

---

## Fase 0 — Preparar o Cloud Shell

Tudo roda no **Azure Cloud Shell** (Bash). Nada de instalar local.

```bash
# 1. Entrar no repo PRIVADO do grupo (onde você trabalha de verdade).
#    Se ainda não clonou no Cloud Shell:
git clone <url-do-repo-privado-do-grupo>
cd <repo-do-grupo>

# 2. Dependências (no Cloud Shell pip --user é permitido)
pip install --user sentence-transformers azure-search-documents \
    azure-storage-blob azure-identity azure-cosmos pyodbc
```

Exportar as variáveis de ambiente a partir dos **outputs do Terraform do lab** (não digite nomes na mão — pegue do estado):

```bash
cd aulas/02-storage-bancos/lab/terraform   # ajuste ao caminho do seu repo

export STORAGE_ACCOUNT_NAME=$(terraform output -raw storage_account_name)
export SEARCH_ENDPOINT=$(terraform output -raw search_endpoint)
export SQL_SERVER="$(terraform output -raw sql_server_name).database.windows.net"
export SQL_DATABASE=$(terraform output -raw sql_database_name)
export COSMOS_ENDPOINT=$(terraform output -raw cosmos_endpoint)
export COSMOS_DATABASE="qcdb"          # confira o nome real do database Cosmos do lab
export COSMOS_CONTAINER="reviews"
```

> Autenticação é **100% Managed Identity** (`DefaultAzureCredential`) — nenhum script tem segredo. Garanta que sua identidade do Cloud Shell tem as roles do lab (Search Index Data Contributor, Storage Blob Data Reader, etc.).

---

## Fase 1 — Exercício 3.1 (vector search)

O lab provisiona AI Search no **SKU `free`**, que **não suporta campo vetorial**. Precisa subir para **Basic** (custa ~US$ 75/mês — destrua depois, ver Fase 5).

```bash
# 1. Editar o SKU do AI Search
#    aulas/02-storage-bancos/lab/terraform/search.tf
#    trocar:   sku = "free"   ->   sku = "basic"
terraform apply        # confirme o plano (só altera o Search service)

# 2. Rodar o script (na raiz da entrega)
cd ../../../../entregas/entrega-02     # ajuste ao seu caminho até entrega-02/
python3 scripts/gerar_embeddings_vector.py
```

**O que capturar:** o script imprime o top-3 de cada uma das 3 queries com os scores reais.
➡️ **Cole os números reais** nas 3 tabelas da seção *3.1 → Parte A* do `entrega-grupo-aula02.md` (substituindo os scores atuais como 0.681 etc.). Se a ordem dos produtos vier diferente, ajuste o texto das observações para refletir o que você viu.

---

## Fase 2 — Exercício 3.2 (Synapse Serverless)

O `terraform/synapse.tf` reaproveita recursos do lab (`random_string.sufixo`, `azurerm_resource_group.rg`, `var.sql_admin_password`). Por isso ele precisa rodar **junto** do Terraform do lab.

```bash
# 1. Copiar o synapse.tf para a pasta do Terraform do lab
cp entregas/entrega-02/terraform/synapse.tf \
   aulas/02-storage-bancos/lab/terraform/

# 2. Aplicar (a senha é sensitive — passe via -var, NUNCA em arquivo)
cd aulas/02-storage-bancos/lab/terraform
terraform apply -var="sql_admin_password=<sua-senha-forte>"
#  cria: conta ADLS Gen2 com HNS (stqclake...), filesystems, Synapse Workspace,
#        firewall rules e o role assignment da Managed Identity.

# 3. Gerar os 3 CSVs de logs e subir ao Lake
cd ../../../../entregas/entrega-02
export STORAGE_ACCOUNT_LAKE="stqclake<sufixo>"   # veja o nome real: terraform output / portal
python3 scripts/gerar_logs_compras.py --upload --account "$STORAGE_ACCOUNT_LAKE"
```

**Rodar a query no Synapse Studio:**
1. Portal → seu Synapse Workspace `syn-qc-<sufixo>` → **Open Synapse Studio**
2. **Develop → SQL script**, conectar ao **Built-in (Serverless)**
3. Colar a query `OPENROWSET` da seção 3.2 (troque `STORAGE` pelo nome real da conta lake)
4. **Run**

**O que capturar:**
- A aba **Messages/Resultados** mostra **"data processed"** → é o número de **bytes processados**.
➡️ Confirme/ajuste o valor na seção *3.2 → Bytes processados* (deve bater no piso de ~10 MB).
- Os agregados por dia/mês já vêm da execução real do gerador — confira os totais.

---

## Fase 3 — Exercício 3.3 (benchmark)

```bash
cd entregas/entrega-02
python3 scripts/benchmark_busca.py
```

**O que capturar:** o script imprime latência média + p95 das 3 estratégias (SQL `LIKE`, Cosmos `CONTAINS`, AI Search vector).
➡️ **Cole as latências reais** na tabela comparativa da seção *3.3*. Os custos fixos (S1, vCores) não mudam — mantenha. Ajuste só as colunas de latência média/p95 se divergirem das faixas atuais.

> Pré-requisito: a tabela `T_PRODUTOS` (SQL) e o container `reviews` (Cosmos) precisam estar populados — use os scripts do lab (`popular_produtos.py`, `popular_reviews.py`, `indexar_produtos.py`) se ainda não rodou.

---

## Fase 4 — Fechar o documento principal

No `entrega-grupo-aula02.md`, revise:

- [ ] **Data de entrega:** trocar `<DD/06/2026>` (topo) pela data real
- [ ] **Turma:** confirmar `1AIER`
- [ ] **3.1** — scores reais colados (Fase 1)
- [ ] **3.2** — bytes processados confirmados (Fase 2)
- [ ] **3.3** — latências reais coladas (Fase 3)
- [ ] Remover as *"Notas de execução"* (rodapés em itálico) **só depois** de ter os números reais — elas existem para sinalizar o que ainda era representativo

---

## Fase 5 — Limpeza (ANTES de gerar o ZIP — evita custo e segredos)

```bash
# Destruir o que custa (Synapse + Lake + Search Basic)
cd aulas/02-storage-bancos/lab/terraform
terraform destroy -var="sql_admin_password=<sua-senha>"
#  ou, para zerar tudo do lab de uma vez:
#  az group delete --name $(terraform output -raw resource_group_name) --yes --no-wait

# Garantir que NÃO há lixo na entrega
cd ../../../../entregas/entrega-02
rm -rf scripts/__pycache__
rm -f arquitetura-qc-aula02.drawio.png   # duplicata; o oficial está em diagramas/
```

**Nunca** inclua no ZIP: `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`, `.venv/`, `~/.cache` do modelo.

---

## Fase 6 — Gerar o ZIP

A estrutura interna deve ser a pasta única `qc-grupo-08-aula02/`.

**Opção A — direto da pasta da entrega (mais simples neste fork):**
```bash
cd entregas/entrega-02
zip -r ~/entrega-grupo-08-aula02.zip . \
   -x "*/__pycache__/*" "*.tfstate*" "*.drawio.png" "INSTRUCOES.md" "GUIA-FINALIZACAO.md"
# confira o conteúdo:
unzip -l ~/entrega-grupo-08-aula02.zip
```

**Opção B — via git archive (se replicar para o repo privado com pasta `aula02/`):**
```bash
cd ~/<repo-do-grupo>
git pull origin main
git archive --format=zip --prefix=qc-grupo-08-aula02/ \
   -o ~/entrega-grupo-08-aula02.zip HEAD:aula02
unzip -l ~/entrega-grupo-08-aula02.zip
```

**Conteúdo esperado do ZIP:**
```
qc-grupo-08-aula02/
├── entrega-grupo-aula02.md       ⭐ documento principal
├── README.md                     como rodar
├── diagramas/arquitetura-qc-aula02.png
├── terraform/synapse.tf
└── scripts/
    ├── gerar_embeddings_vector.py
    ├── gerar_logs_compras.py
    └── benchmark_busca.py
```

Tamanho ideal < 5 MB (o diagrama PNG tem ~190 KB, ok).

---

## Fase 7 — Subir no Portal FIAP

- **Apenas 1 membro** do grupo faz o upload (combine antes — evita duplicar)
- Tarefa: **"Entrega Aula 2"**
- **Prazo:** 1 dia antes da Aula 3

---

## Checklist final

| ✅ | Item |
|----|------|
| ☐ | N1 (1.1–1.4) — já pronto |
| ☐ | N2 (2.1, 2.2, 2.3) + diagrama — já pronto |
| ☐ | N3 3.1 com **scores reais** colados |
| ☐ | N3 3.2 com **bytes processados** confirmados |
| ☐ | N3 3.3 com **latências reais** coladas |
| ☐ | Notas de execução removidas (após números reais) |
| ☐ | Data + turma preenchidas |
| ☐ | Reflexão coletiva — já pronta |
| ☐ | `terraform destroy` feito (sem custo correndo) |
| ☐ | ZIP gerado e conferido com `unzip -l` |
| ☐ | Sem `tfstate`/segredos/`__pycache__` no ZIP |
| ☐ | Upload por 1 membro só, dentro do prazo |
