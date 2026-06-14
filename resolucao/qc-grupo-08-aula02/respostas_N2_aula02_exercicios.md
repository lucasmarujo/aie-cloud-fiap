# Exercícios — Aula 2

**Tema:** Storage & Bancos de Dados na Nuvem
**Formato:** **Entrega obrigatória por grupo** — ZIP no Portal FIAP
**Vale:** 10% da nota final ([rubrica completa](../../entregas/rubrica.md))
**Prazo:** 1 dia antes da Aula 3
**Como entregar:** ver [entregas/entrega-02/INSTRUCOES.md](../../entregas/entrega-02/INSTRUCOES.md)

---

## Instruções gerais

Esta é a **2ª entrega de grupo** da disciplina. Os 3 níveis são **divisão de trabalho dentro do grupo**, não escolha livre:

- 🟢 **Nível 1 — Básico:** consolida storage, tiers, relacional vs NoSQL, RBAC do Key Vault
- 🟡 **Nível 2 — Intermediário:** modelagem de dados QC + plano de migração + particionamento Cosmos
- 🔴 **Nível 3 — Avançado:** **bônus opcional** — vector search verdadeira (embeddings), Synapse serverless, benchmark Cosmos vs SQL vs AI Search

**Mínimo obrigatório:** N1 + N2 cobertos. **N3 é bônus** (até +2 pts extras).

### Distribuição entre membros do grupo (sugerida)

- Iniciantes em cloud: N1 (consolidação)
- Intermediários: N2 (bloco QC — matriz de decisão e plano de migração)
- Experientes: N3 (bônus) — vector search é o tópico mais técnico

> **Rodízio:** quem fez N1 na Aula 1 deve preferencialmente fazer N2 ou N3 agora. Vale ponto da rubrica (Critério 4 — Colaboração).

### Template obrigatório

Use o [template em `entregas/template-entrega-grupo.md`](../../entregas/template-entrega-grupo.md) para o `entrega-grupo-aula02.md` dentro do ZIP.

> **Política "no install":** Tudo roda no Azure Cloud Shell. `pip install --user` é OK no Cloud Shell.

---

## 🟢 Nível 1 — Básico: Consolidando os Fundamentos

### Exercício 1.1 — Tipos de Storage

Para cada cenário, escolha **Object Storage**, **File Storage** ou **Block Storage** e justifique em uma frase.

| Cenário | Tipo | Justificativa |
|---------|------|---------------|
| Hospedar imagens de produtos do e-commerce QC (5M de SKUs) | | |
| Disco onde roda o sistema operacional de uma VM de banco | | |
| Pasta compartilhada entre 10 VMs de um time de DevOps | | |
| Backup mensal de bancos de dados (retenção 7 anos) | | |
| Storage de modelos `.pkl` do time de ML para serving | | |
| Dump diário de logs de aplicação para análise futura | | |

<details>
<summary>Gabarito sugerido</summary>

- Imagens de produtos: **Object** (volume alto, acesso via HTTP, sem necessidade de sistema de arquivos)
- Disco da VM de banco: **Block** (baixa latência, atrelado a uma VM)
- Pasta compartilhada entre VMs: **File** (montável em múltiplas VMs simultaneamente como `/mnt/dados`)
- Backup com 7 anos: **Object com Archive tier** (custo baixíssimo, acesso raro)
- Modelos `.pkl` para serving: **Object** (downloads via HTTP, versionamento por blob)
- Logs para análise: **Object com lifecycle Hot→Cool→Archive** (analytics serverless sobre Blob)

</details>

---

### Exercício 1.2 — Tiers de acesso (cálculo)

A Quantum Commerce armazena **2 TB de logs de compras**. Os primeiros 30 dias os logs são consultados para detecção de fraude (Hot). Depois disso, viram dados arquivados de compliance LGPD (Archive, retenção 5 anos).

a) Quanto custaria 1 mês desses logs **se mantidos 100% em Hot tier**? (Use ~$0,018/GB/mês)
b) Quanto custaria 1 mês desses logs **com lifecycle: 30 dias Hot + Archive depois**? (Archive ~$0,002/GB/mês)
c) Economia anual com a lifecycle policy?

<details>
<summary>Gabarito</summary>

- a) 2.048 GB × $0,018 = **$36,86/mês** (~$442/ano)
- b) Dados estão sempre em Archive depois de 30 dias. Considerando steady state, ~96,7% em Archive:
  - Hot: 2048 × 30/365 × $0,018 = $3,03/mês (média anual)
  - Archive: 2048 × 335/365 × $0,002 = $3,76/mês (média anual)
  - Total: ~**$6,79/mês**
- c) Economia anual: ($36,86 - $6,79) × 12 = **~$360/ano**

> Para a QC com volumes reais (centenas de TB), essa decisão impacta facilmente seis dígitos por ano.

</details>

---

### Exercício 1.3 — Relacional vs NoSQL

Para cada caso de uso da Quantum Commerce, marque qual tipo de banco é mais adequado e justifique:

| Caso de uso | Relacional (Azure SQL) | NoSQL doc (Cosmos) | Vector DB (AI Search) | Justificativa |
|-------------|------------------------|--------------------|-----------------------|---------------|
| Carrinho de compras ativo do usuário | | | | |
| Catálogo de produtos com SKU, preço, estoque | | | | |
| Reviews dos clientes (texto livre + score) | | | | |
| "Encontre produtos similares a este" (recomendação) | | | | |
| Histórico de pedidos para faturamento | | | | |
| Sessão do usuário (chave-valor, expira em 30min) | | | | |
| Logs de comportamento de navegação | | | | |

<details>
<summary>Sugestões</summary>

- Carrinho ativo: **NoSQL doc** (esquema variável, leitura rápida, expira)
- Catálogo: **Relacional** (esquema fixo, joins com categorias, integridade de estoque)
- Reviews: **NoSQL doc** (texto livre, sem schema rígido)
- Recomendação: **Vector DB** (similaridade semântica)
- Histórico de pedidos: **Relacional** (ACID, faturamento exige garantias)
- Sessão (key-value): **Redis** ou **Cosmos com TTL** (não cabe perfeitamente nas opções, mas Cosmos é o mais próximo)
- Logs de navegação: **NoSQL** ou Object Storage + Synapse — depende do uso analítico

</details>

---

### Exercício 1.4 — Key Vault e RBAC

Você acabou de provisionar o Key Vault da Aula 2. Para cada perfil, escolha a role built-in e justifique:

| Perfil | Role no Key Vault | Justificativa |
|--------|-------------------|---------------|
| Você (criador do Vault, faz dev e ops) | | |
| Azure Function que consulta `T_PRODUTOS` precisa ler a connection string | | |
| Engenheiro de segurança que audita os segredos sem alterá-los | | |
| Pipeline de CI/CD que injeta novos segredos automaticamente | | |
| Time de FinOps que precisa ver custo do Vault sem ver segredos | | |

**Referência:** [Azure Built-in Roles — Key Vault](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#key-vault)

<details>
<summary>Sugestões</summary>

- Você: **Key Vault Secrets Officer** (CRUD em segredos — sem precisar de Owner)
- Function lendo segredos: **Key Vault Secrets User** (só leitura no plano de dados de segredos) — via Managed Identity
- Auditor: **Key Vault Reader** (lê metadados, não os valores)
- CI/CD injetando segredos: **Key Vault Secrets Officer** com escopo limitado (idealmente Service Principal dedicado)
- FinOps: **Reader** no Resource Group (vê custo no Cost Management, não acessa Vault)

</details>

---

## 🟡 Nível 2 — Intermediário: Decisões Arquiteturais

### Exercício 2.1 — Modelagem de dados da QC (em grupo)

A Quantum Commerce tem os seguintes domínios:

- **Produtos** (catálogo: 5M SKUs)
- **Clientes** (~50M de clientes ativos, perfil + endereço + preferências)
- **Pedidos** (~10M/mês, alta criticidade transacional)
- **Carrinhos ativos** (~500k a qualquer momento, expiram em 24h)
- **Reviews** (~30M de textos livres, alimentam análise de sentimento)
- **Busca de produtos** (consultas dos agentes + frontend)
- **Sessões de usuário** (~1M ativas)
- **Histórico de navegação** (clickstream — bilhões de eventos)
- **Modelos de ML** (recomendação, classificação, predição de churn)

**Sua tarefa:** Preencha a matriz de decisão abaixo:

| Domínio | Serviço Azure escolhido | SKU/Configuração | Justificativa |
|---------|--------------------------|-------------------|----------------|
| **Produtos** | Azure SQL Database (Hyperscale) | Hyperscale, 4 vCores, leitura replicada | Catálogo de 5M SKUs tem esquema fixo (preço, estoque, categoria) e exige integridade referencial com pedidos. É a evolução da `T_PRODUTOS` provisionada no `sql.tf` do lab. Hyperscale escala storage até 100TB sem downtime, e réplicas de leitura suportam o alto volume de consultas do frontend e dos agentes. *Nota de transição: o plano de migração (2.2) propõe Azure SQL Managed Instance (General Purpose) como destino imediato do Oracle on-prem — Hyperscale é a arquitetura-alvo de longo prazo, após o domínio Produtos amadurecer fora do core transacional do MI.* |
| **Clientes** | Azure SQL Database (Business Critical) | Business Critical, 4 vCores, zona redundante | Dados de 50M de clientes (perfil, endereço, preferências) exigem ACID para consistência de cadastro e zona redundante para alta disponibilidade — base para faturamento e LGPD. Mesma nota de transição do domínio Produtos: MI (General Purpose) no destino imediato da migração, Business Critical como alvo de longo prazo. |
| **Pedidos** | Azure SQL Database (Hyperscale) + Azure Service Bus | Hyperscale, 8 vCores + Service Bus Premium | 10M pedidos/mês com alta criticidade transacional exigem ACID. O Service Bus desacopla o registro do pedido do processamento downstream (pagamento, logística, notificação) via eventos. *Consistente com 2.2: o destino imediato da migração já é Business Critical (MI) para Pedidos, dado o nível de criticidade — aqui mantemos Business Critical mas evoluindo para Hyperscale conforme o volume de SKUs e leituras analíticas cresce.* |
| **Carrinhos ativos** | Azure Cosmos DB (API NoSQL) | Serverless/autoscale 400-4000 RU/s, TTL = 24h | ~500k carrinhos ativos com esquema variável (itens, cupons, frete calculado). O TTL nativo do Cosmos expira automaticamente os carrinhos abandonados após 24h, sem job de limpeza. É a mesma conta Cosmos Serverless do `cosmos.tf` do lab, em container dedicado. **Por que não Azure SQL?** esquema de carrinho varia por campanha/promoção — modelar isso em tabelas relacionais exigiria migrações de schema frequentes; Cosmos absorve a variação naturalmente. |
| **Reviews** | Azure Cosmos DB (API NoSQL) | Autoscale 1000-10000 RU/s, particionado por `produto_id` | 30M de textos livres com schema flexível (título, score, conteúdo, metadados). Particionamento por `produto_id` agrupa reviews do mesmo produto, otimizando a leitura por página de produto (ver detalhamento em 2.3). É o container `reviews` do `cosmos.tf` do lab, escalado de Serverless para Autoscale dado o volume de produção. |
| **Busca de produtos** | Azure AI Search | Standard S1, índice vetorial + semantic ranker | Consultas dos agentes de IA e do frontend exigem busca semântica além de busca por palavra-chave. *Nota: o lab da Aula 2 provisiona AI Search em SKU Free com semantic search (sem vector — vector real é o Exercício 3.1). Em produção, com 5M de SKUs, a QC exigiria Standard S1+ com vector search habilitado para RAG completo.* **Por que não ficar no Free tier?** Free limita a 3 índices e 50MB — inviável para 5M de SKUs + 30M de reviews indexados; S1 suporta até 12 réplicas/12 partições para escalar throughput de busca nos picos de tráfego. |
| **Sessões** | Azure Cache for Redis | Premium P1, cluster habilitado | ~1M sessões ativas exigem latência sub-milissegundo. Redis é o padrão de mercado para sessão de usuário, com TTL nativo e throughput muito superior ao Cosmos para esse padrão de acesso. **Por que não Cosmos com TTL** (como usamos para Carrinhos)? Sessão tem volume de leitura/escrita muito maior por usuário (a cada request) e vida útil curtíssima (30min) — no Cosmos, esse padrão geraria custo de RU desproporcional ao valor do dado; Redis em memória é ordens de magnitude mais barato para esse perfil de acesso. |
| **Histórico de navegação (clickstream)** | Azure Event Hubs + ADLS Gen2 (via Synapse) | Event Hubs Standard + ADLS Gen2 em Parquet | Bilhões de eventos exigem ingestão em streaming de alto throughput e armazenamento de baixo custo em formato colunar para análises via Synapse Serverless (Exercício 3.2), sem banco transacional. **Por que não Cosmos?** mesmo com TTL, o volume de bilhões de eventos/dia tornaria o custo de RU de gravação proibitivo; Blob+Parquet é ~10x mais barato por GB e o padrão de consulta (agregações analíticas, não lookups pontuais) é exatamente o caso de uso do Synapse Serverless (OLAP, ver apostila Bloco 4). |
| **Modelos de ML** | Azure Blob Storage + Azure Machine Learning (Model Registry) | Container `modelos` (Hot tier) + AML Workspace | Modelos versionados (.pkl, .onnx); o Model Registry controla versões e linhagem. Os 3 containers do lab (`catalogo`, `imagens`, `logs`) têm propósitos definidos — modelos exigem um 4º container dedicado (`modelos`), seguindo o mesmo padrão de organização por prefixo/container do `storage.tf`. |

**Diagrama:** ver `diagramas/arquitetura-qc-aula02.png`. Representa os 9 domínios conectados: o AKS (Aula 01) escreve em Azure SQL (Produtos, Clientes, Pedidos) e Cosmos DB (Carrinhos, Reviews); o Redis atende sessões; o Event Hubs captura clickstream e alimenta o ADLS Gen2, consultado via Synapse Serverless; o AI Search indexa Produtos + Reviews; e o AML consome dados do ADLS Gen2 para treinar modelos, publicando artefatos no Blob.


---

---

### Exercício 2.3 — Particionamento no Cosmos DB

No lab da Aula 2, o container `reviews` foi particionado por `produto_id`. Responda:

**a) Por que NÃO seriam boas partitioning keys**

**`id` da review:**
1. Fan-out total em queries por produto — cada review numa partição própria exigiria cross-partition query para "todas as reviews do produto X".
2. Sem agrupamento lógico — o `id` é um GUID arbitrário, sem relação com o padrão de acesso real.
3. Overhead de gerenciamento — o Cosmos criaria milhões de partições lógicas com 1 item cada.

**`score` (1-5):**
1. Cardinalidade extremamente baixa (5 valores) — cria hot partitions, já que a maioria das reviews tende a ter score 5, concentrando RU/s.
2. Tamanho da partição estoura o limite de 20 GB — com 30M de reviews em só 5 valores, cada partição lógica facilmente ultrapassaria 20 GB.

**`data_da_review` (timestamp):**
1. Hot partition no presente — todas as escritas recentes cairiam na mesma partição (a data de hoje), gargalando a escrita.
2. Queries por produto continuam ineficientes — reviews do mesmo produto ficariam espalhadas por múltiplas datas/partições.

**b) Por que `produto_id` funciona razoavelmente bem — e qual o problema**

Funciona bem porque o padrão de acesso dominante é "ler todas as reviews de um produto específico" (página de produto) — o Cosmos resolve isso numa única consulta dentro de uma única partição lógica, sem fan-out.

**O problema:** produtos best-sellers podem acumular dezenas de milhares de reviews, criando uma **partição quente (hot partition)** e potencialmente excedendo os 20 GB de limite por partição lógica. Produtos com poucas reviews ficam em partições pequenas e subutilizadas — distribuição desigual de dados e de RU/s entre partições físicas.

**c) Estratégia para "todas as reviews de um cliente específico" — Hierarchical Partition Keys**

Usar **hierarchical partition keys** (Cosmos, desde 2023), com chave composta de até 3 níveis:

```
PartitionKey = /produto_id, /cliente_id
```

Consultas por `produto_id` continuam eficientes; consultas combinando `produto_id` + `cliente_id` atingem uma única partição física. Para "todas as reviews de um cliente, independente do produto", a hierarchical key sozinha não resolve — seria necessário um índice secundário (container separado ou índice no AI Search) mapeando `cliente_id → lista de produto_ids/review_ids`, permitindo lookup inicial seguido de consultas pontuais.

**d) Estimativa de tamanho de partição — produto com 50.000 reviews**

Assumindo tamanho médio por documento de ~1 KB (consistente com o limite de ~1k caracteres do campo `content` na base Amazon Polarity):

```
Tamanho da partição = 50.000 reviews × 1 KB = 50.000 KB ≈ 48,8 MB
Quota por partição lógica do Cosmos: 20 GB = 20.480 MB
Percentual da quota: 48,8 / 20.480 ≈ 0,24%
```

**Conclusão:** para 50.000 reviews de ~1 KB cada, a partição usa apenas ~0,24% da quota de 20 GB — confortável. O problema do item b) só se manifestaria em casos extremos: um produto precisaria de mais de 20 milhões de reviews para estourar a quota — cenário improvável, mas que reforça a importância de **monitorar o crescimento das partições mais populares**, especialmente se o tamanho médio do documento crescer (reviews com imagens, respostas do vendedor).

---

## 🔴 Nível 3 — Avançado: Vector Search Real e Analytics

### Exercício 3.1 — Vector search verdadeira no AI Search

O lab usou `semantic_search`. Vamos agora fazer **vector search real** gerando embeddings.

**Tudo no Cloud Shell — sem instalação local.**

#### Parte A — Gerar embeddings

Como a disciplina é Cloud (e Azure OpenAI não está no escopo padrão), use a biblioteca `sentence-transformers` que roda local no Cloud Shell:

```bash
pip install --user sentence-transformers azure-search-documents azure-storage-blob azure-identity
```

> ⚠️ Sentence Transformers baixa modelo de ~80MB no primeiro uso — vai para `~/.cache` no storage persistente do Cloud Shell.

Script:

```python
"""
Gera embeddings dos produtos e indexa no AI Search com campo vector.
Requer: pip install --user sentence-transformers azure-search-documents
"""
import os, csv
from sentence_transformers import SentenceTransformer
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchField,
    SearchFieldDataType, VectorSearch, HnswAlgorithmConfiguration,
    VectorSearchProfile,
)
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient

DIMENSION = 384  # all-MiniLM-L6-v2 produz vetores 384-dim
INDEX_NAME = "produtos-vector-index"

def main():
    endpoint = os.environ["SEARCH_ENDPOINT"]
    storage = os.environ["STORAGE_ACCOUNT_NAME"]
    credential = DefaultAzureCredential()

    print("→ Carregando modelo de embedding...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Baixar produtos
    blob = BlobServiceClient(f"https://{storage}.blob.core.windows.net", credential=credential)
    csv_text = blob.get_blob_client("catalogo", "produtos.csv").download_blob().readall().decode("utf-8")
    rows = list(csv.DictReader(csv_text.splitlines()))

    # Gerar embeddings de "nome + descricao"
    print(f"→ Gerando embeddings de {len(rows)} produtos...")
    textos = [f"{r['nome']}. {r['descricao']}" for r in rows]
    embeddings = model.encode(textos).tolist()
    print(f"✓ Embeddings gerados (dim={len(embeddings[0])})")

    # Definir índice com campo vector
    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
    index = SearchIndex(
        name=INDEX_NAME,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="nome", type=SearchFieldDataType.String),
            SearchableField(name="descricao", type=SearchFieldDataType.String),
            SimpleField(name="categoria", type=SearchFieldDataType.String, filterable=True),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=DIMENSION,
                vector_search_profile_name="produtos-hnsw-profile",
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="produtos-hnsw")],
            profiles=[VectorSearchProfile(name="produtos-hnsw-profile", algorithm_configuration_name="produtos-hnsw")],
        ),
    )
    try: index_client.delete_index(INDEX_NAME)
    except: pass
    index_client.create_index(index)

    # Indexar
    search_client = SearchClient(endpoint=endpoint, index_name=INDEX_NAME, credential=credential)
    docs = [
        {
            "id": r["id"], "nome": r["nome"], "descricao": r["descricao"],
            "categoria": r["categoria"], "content_vector": embeddings[i],
        }
        for i, r in enumerate(rows)
    ]
    search_client.upload_documents(docs)
    print(f"✓ {len(docs)} produtos indexados com vetores")

    # Busca por vetor: gerar embedding da query e buscar nearest
    queries = [
        "preciso de uma cadeira boa para minha coluna",
        "algo para acompanhar séries",
        "presente para um amigo que ama café",
    ]
    for q in queries:
        q_vec = model.encode(q).tolist()
        print(f"\n=== Vector search: '{q}' ===")
        results = search_client.search(
            search_text=None,
            vector_queries=[{
                "kind": "vector",
                "vector": q_vec,
                "k_nearest_neighbors": 3,
                "fields": "content_vector",
            }],
        )
        for r in results:
            print(f"  [{r['@search.score']:.4f}] {r['nome']}")

if __name__ == "__main__":
    main()
```

**Tarefa:** Execute, registre os resultados das 3 queries no `respostas-aula02.md` e **compare** com o semantic search do lab (parte B). Qual deu resultados mais relevantes? Onde cada um falha?

#### Parte B — Reflexão

Responda no `respostas-aula02.md`:

1. Por que o modelo `all-MiniLM-L6-v2` é uma má escolha para produção da Quantum Commerce? (Dica: língua portuguesa, latência, qualidade)
2. Que serviço da Azure você usaria para gerar embeddings em produção? (Dica: Azure OpenAI text-embedding-3-large)
3. Como você manteria os embeddings atualizados quando produtos novos chegam? (Pipeline incremental)
4. Quanto custaria gerar embeddings para 5M de produtos da QC com Azure OpenAI? (Pesquise os preços)

---

### Exercício 3.2 — Synapse Serverless: query sobre Blob

A QC armazenou os `logs de compras` em formato Parquet no Blob. Em vez de carregar tudo num DWH, vamos usar **Synapse Serverless SQL Pool** para queryar direto no Blob (zero ETL).

#### Setup

Adicione ao Terraform (crie `lab/terraform/synapse.tf` no seu fork):

```hcl
resource "azurerm_synapse_workspace" "qc" {
  name                                 = "synapse-qc-${random_string.sufixo.result}"
  resource_group_name                  = azurerm_resource_group.rg.name
  location                             = azurerm_resource_group.rg.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.synapse.id
  sql_administrator_login              = "synadmin"
  sql_administrator_login_password     = var.sql_admin_password
  identity { type = "SystemAssigned" }
  tags = local.tags
}

# Synapse precisa de Data Lake Storage Gen2
resource "azurerm_storage_data_lake_gen2_filesystem" "synapse" {
  name               = "synapsefs"
  storage_account_id = azurerm_storage_account.qc.id   # precisa de is_hns_enabled=true
}

resource "azurerm_synapse_firewall_rule" "all_azure" {
  name                 = "AllowAzure"
  synapse_workspace_id = azurerm_synapse_workspace.qc.id
  start_ip_address     = "0.0.0.0"
  end_ip_address       = "0.0.0.0"
}
```

> ⚠️ Synapse requer Storage com HNS habilitado: no `azurerm_storage_account` adicione `is_hns_enabled = true`. Isso impede algumas features de Blob clássico — leia a doc.

#### Gerar dados de exemplo

Crie 3 arquivos `logs_compras_jan.csv`, `_fev.csv`, `_mar.csv` com 1000 registros cada (script no `respostas-aula02.md`) e faça upload ao Blob.

#### Query no Synapse

1. No portal, abrir o Synapse Studio
2. Conectar ao Serverless SQL Pool
3. Executar:

   ```sql
   SELECT
     CAST(periodo AS DATE) AS dia,
     COUNT(*)              AS pedidos,
     SUM(valor)            AS receita
   FROM OPENROWSET(
     BULK 'https://STORAGE.blob.core.windows.net/logs/compras_*.csv',
     FORMAT = 'CSV',
     PARSER_VERSION = '2.0',
     FIRSTROW = 2
   ) WITH (periodo VARCHAR(20), valor DECIMAL(10,2)) AS dados
   GROUP BY CAST(periodo AS DATE)
   ORDER BY dia;
   ```

4. **Reporte:** quantos bytes Synapse processou na query? (visível na aba "Resultados")

#### Reflexão

Responda no `respostas-aula02.md`:

1. Por que Synapse Serverless faz sentido para a QC em vez de Synapse Dedicated Pool?
2. Qual o custo de query: 5 TB processados/mês a $5 por TB?
3. Como reduzir custo por query? (Dica: Parquet + partições)

---

### Exercício 3.3 — Benchmark: Cosmos vs SQL vs AI Search

Para a query "buscar produto que melhor responde à pergunta `cadeira ergonômica para dor lombar`", você tem 3 opções na QC:

a) **Azure SQL** com `LIKE '%cadeira%'` e filtros sobre categoria/preço
b) **Cosmos DB** com índice full-text (Cosmos não tem nativo — precisa Azure AI Search externo)
c) **Azure AI Search** com semantic ranking ou vector search

**Tarefa:**

1. Implemente as 3 versões (você já tem AI Search no lab — adicione versão SQL e Cosmos)
2. Meça latência média de 10 queries em cada
3. Compare **qualidade** das respostas (subjetivamente — quem traria o produto certo?)
4. Compare **custo** projetado: 1M queries/mês em cada
5. **Recomende** qual usar para o agente de busca da QC

Entrega: tabela comparativa + recomendação justificada no `respostas-aula02.md`.

---

## Critérios de entrega

A entrega é **um ZIP por grupo** (`entrega-grupo-NN-aula02.zip`) no Portal FIAP. Estrutura completa, prazo e dicas de geração do ZIP em [entregas/entrega-02/INSTRUCOES.md](../../entregas/entrega-02/INSTRUCOES.md).

| Item | Obrigatório? | Pontos máximos |
|------|--------------|----------------|
| Cabeçalho do grupo + distribuição do trabalho | ✅ Sim | 1 pt (Critério 4) |
| 🟢 N1 — Exercícios 1.1, 1.2, 1.3, 1.4 respondidos | ✅ Sim | 3 pts (Critério 1) |
| 🟡 N2 — 2.1 (matriz + diagrama), 2.2 (migração), 2.3 (particionamento Cosmos) | ✅ Sim | 3 pts (Critério 2) + 2 pts qualidade técnica (Critério 3) |
| 🔴 N3 — 3.1 (vector search verdadeira), 3.2 (Synapse), 3.3 (benchmark) | 🎁 Bônus | até +2 pts extras |
| Reflexão coletiva ao final | ✅ Sim | 1 pt (Critério 5) |
| **Total da entrega** | | **10 pts** (10% da nota final) |

**Prazo:** 1 dia antes da Aula 3.
**Onde:** upload do ZIP no Portal FIAP. Apenas 1 membro do grupo faz o upload.
