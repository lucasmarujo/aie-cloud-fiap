# Entrega Aula 02 — Grupo 08

**Disciplina:** Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents
**Turma:** 1AIER
**Data de entrega:** <DD/06/2026>

## Grupo

| # | Nome completo | GitHub | E-mail FIAP |
|---|---------------|--------|-------------|
| 1 | Tatiana Mastrogiovanni Haddad | https://github.com/TatiHaddad | rm373809@fiap.com.br |
| 2 | Luciana Chaves D'Olivo | https://github.com/l-cdolivo | rm371277@fiap.com.br |
| 3 | Lucas Marujo Amadeu | https://github.com/lucasmarujo | rm370469@fiap.com.br |


## Distribuição do trabalho

| Membro | Nível assumido | Item específico |
|--------|----------------|-----------------|
| Lucas Marujo Amadeu | 🟢 N1 + 🟡 N2 (parcial) | Exercícios 1.1, 1.2, 1.3, 1.4 + 2.2 (plano de migração) |
| Tatiana Mastrogiovanni Haddad | 🟡 N2 + coordenação | Exercício 2.1 (matriz + diagrama) + 2.3 (particionamento Cosmos); montagem do documento, reflexão e ZIP |
| Luciana Chaves D'Olivo | 🔴 N3 (bônus) | Exercícios 3.1 (vector search), 3.2 (Synapse Serverless) e 3.3 (benchmark — script escrito, não testado) |

> **Rodízio (Critério 4):** na Aula 1, Lucas assumiu N2 + N3; nesta entrega ele rotaciona para N1 + parte do N2 (2.2). Tatiana, que assumiu N2 + coordenação na Aula 1, mantém o bloco de arquitetura de dados (2.1 + 2.3) e a coordenação. Luciana assume o N3 bônus completo.

---

## 🟢 Nível 1 — Respostas

*Responsável: Lucas Marujo Amadeu — Exercícios 1.1, 1.2, 1.3, 1.4.*

### Exercício 1.1 — Tipos de Storage

| Cenário | Tipo | Justificativa |
|---------|------|----------------|
| Imagens de produtos do e-commerce QC (5M de SKUs) | **Object (Blob)** | Volume massivo, acesso por URL/HTTP, sem necessidade de sistema de arquivos; serve direto a CDN e é barato por GB. |
| Disco onde roda o SO de uma VM de banco | **Block (Managed Disk / Premium SSD)** | Banco exige baixíssima latência e I/O em blocos; o disco é atrelado a uma VM e montado como dispositivo de bloco. |
| Pasta compartilhada entre 10 VMs de DevOps | **File (Azure Files — SMB/NFS)** | Único tipo montável simultaneamente por várias VMs como `/mnt/dados`, com semântica de sistema de arquivos. |
| Backup mensal de bancos (retenção 7 anos) | **Object — Archive tier** | Custo por GB mais baixo da plataforma para dado de acesso raro; 7 anos = compliance, não consulta frequente. |
| Modelos `.pkl` do time de ML para serving | **Object (Blob)** | Download via HTTP pelo runtime de serving, versionamento por blob/prefixo, sem precisar de FS nem de VM dedicada. |
| Dump diário de logs para análise futura | **Object — lifecycle Hot→Cool→Archive** | Ingestão append-only barata; analytics serverless (Synapse) consulta direto no Blob, sem ETL para um banco. |

**Observações de implementação:** Object ≠ File ≠ Block não é só preço — é o *modelo de acesso*. Object é chave→objeto via API/HTTP (escala "infinita", sem POSIX); File dá POSIX/SMB compartilhado; Block é o mais "cru" e rápido, mas amarrado a uma máquina. No caso do Archive tier (backup 7 anos): atenção ao **mínimo de 180 dias** de permanência (deletar antes gera *early-deletion fee*) e à **reidratação**, que tem latência de horas + custo extra. Os logs e as imagens são exatamente os dois containers do lab da QC (`logs/` com lifecycle e `catalogo`/`imagens` no Blob) — a escolha aqui é o que já está provisionado no `storage.tf`.

### Exercício 1.2 — Tiers de acesso (cálculo)

**Dado:** 2 TB de logs de compras = 2.048 GB. Primeiros 30 dias em Hot (detecção de fraude), depois Archive (compliance LGPD, 5 anos). Preços: Hot ≈ $0,018/GB·mês, Archive ≈ $0,002/GB·mês.

**a) Custo de 1 mês 100% em Hot tier:**
```
2.048 GB × $0,018 = $36,86/mês (≈ $442/ano)
```

**b) Custo de 1 mês com lifecycle (30 dias Hot + Archive depois):**

Em regime estacionário (ingestão contínua: a cada dia entra log novo em Hot e sai log velho para Archive), em média 30/365 do volume está em Hot e 335/365 em Archive:

| Tier | Fração | Cálculo | Custo médio |
|------|--------|---------|-------------|
| Hot | 30/365 (≈8,2%) | 2.048 × (30/365) × $0,018 | $3,03/mês |
| Archive | 335/365 (≈91,8%) | 2.048 × (335/365) × $0,002 | $3,76/mês |
| **Total** | | | **≈ $6,79/mês** |

**c) Economia anual com a lifecycle policy:**
```
($36,86 - $6,79) × 12 = $30,07 × 12 ≈ $360/ano
```

**Leitura de FinOps:** a economia *percentual* é o que escala — Hot custa 9× o Archive ($0,018 vs $0,002). O valor absoluto aqui é pequeno porque o exercício usa 2 TB num único mês. Com retenção real de 5 anos e ingestão diária, a QC acumula centenas de TB em Archive — a mesma policy economiza facilmente seis dígitos por ano. O cálculo (b) é um modelo simplificado de steady-state: o ponto que importa é o raciocínio — dado quente fica caro parado, mover automaticamente para Archive após a janela de uso ativo (30 dias) é decisão de FinOps, não de código. Trade-off honesto: Archive tem custo/latência de reidratação e mínimo de 180 dias — compensa para logs de compliance quase nunca lidos, não para algo consultado com frequência.

### Exercício 1.3 — Relacional × NoSQL × Vector

| Caso de uso | Banco | Justificativa |
|-------------|-------|----------------|
| Carrinho de compras ativo | **NoSQL doc (Cosmos)** | Esquema variável (itens heterogêneos), leitura/escrita rápida por chave do usuário e expira sozinho com TTL (24h). |
| Catálogo de produtos (SKU, preço, estoque) | **Relacional (Azure SQL)** | Esquema fixo, joins com categorias/fornecedores e integridade de estoque exigem ACID. É a `T_PRODUTOS` do lab. |
| Reviews dos clientes (texto livre + score) | **NoSQL doc (Cosmos)** | Texto livre sem schema rígido, campos opcionais, alta cardinalidade de escrita. É o container `reviews` do lab. |
| "Encontre produtos similares a este" | **Vector DB (AI Search)** | Recomendação = similaridade semântica entre embeddings; nem SQL nem documento resolvem `LIKE`/igualdade. |
| Histórico de pedidos para faturamento | **Relacional (Azure SQL)** | Faturamento exige ACID e garantias transacionais (consistência forte, auditável). Erro aqui é erro fiscal. |
| Sessão do usuário (chave-valor, expira 30min) | **Cosmos com TTL** (ideal: Redis) | Padrão é cache key-value de baixíssima latência → Azure Cache for Redis. Dentro das opções dadas, Cosmos com TTL é o mais próximo. |
| Logs de comportamento de navegação | **Object Storage + Synapse** (ou NoSQL) | Clickstream = bilhões de eventos, append-only. Mais barato gravar no Blob e consultar com analytics serverless do que manter num banco operacional. |

**Nuances:** a resposta tecnicamente certa para "key-value que expira em 30 min" é Redis (cache em memória, latência sub-ms); marcamos Cosmos+TTL por ser o mais próximo dentro das 3 opções dadas, mas em produção a QC usaria Redis. Vector não substitui relacional: recomendação usa Vector, mas o preço/estoque do produto recomendado ainda vem do SQL — é exatamente o RAG dos agentes. Cosmos aparece 3× (carrinho, reviews, sessão), cada um por um motivo diferente (esquema variável, texto livre, TTL) — não é "Cosmos para tudo", é Cosmos onde não há necessidade de join nem de ACID.

### Exercício 1.4 — Key Vault e RBAC

| Perfil | Role no Key Vault | Justificativa |
|--------|-------------------|----------------|
| Você (criador do Vault, faz dev e ops) | **Key Vault Secrets Officer** | CRUD completo no plano de dados de segredos sem precisar ser Owner do recurso. |
| Azure Function que lê a connection string de `T_PRODUTOS` | **Key Vault Secrets User** | Só leitura do valor do segredo, via Managed Identity da Function. |
| Engenheiro de segurança que audita sem alterar | **Key Vault Reader** | Lê metadados (quais segredos existem, versões, datas), mas não o valor. |
| Pipeline de CI/CD que injeta novos segredos | **Key Vault Secrets Officer** (escopo limitado) | Precisa criar/atualizar segredos, via Service Principal/Workload Identity dedicado e escopo no Vault específico. |
| FinOps que precisa ver custo sem ver segredos | **Reader no Resource Group** (+ Cost Management Reader) | Vê custo no Cost Management e metadados do recurso, sem qualquer acesso ao plano de dados do Vault. |

**Por que isso é o coração de uma plataforma agentic:** a diferença Secrets Officer × Secrets User × Reader é o menor privilégio aplicado — quem opera o Vault ≠ quem só lê um segredo em runtime ≠ quem só audita. Managed Identity > segredo em arquivo: a Function não guarda a connection string, ela se autentica com sua identidade gerenciada e o `DefaultAzureCredential` resolve o token. Quando um agente de IA roda numa Function e lê dados do SQL, é esse mesmo mecanismo que impede a credencial de escapar para o prompt/log. O Vault do lab usa RBAC habilitado (não Access Policies legadas); em produção, purge protection ligado + segregação dessas roles é o que transforma "segredo hardcoded" num modelo auditável.

---

## 🟡 Nível 2 — Respostas + Implementação

### Exercício 2.1 — Modelagem de dados da Quantum Commerce

*Responsável: Tatiana Mastrogiovanni Haddad.*

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

### Exercício 2.2 — Plano de migração de dados (12 meses)

*Responsável: Lucas Marujo Amadeu.*

**Situação atual da Quantum Commerce:**

| Repositório atual | Volume | Conteúdo |
|---|---|---|
| Oracle on-premise | 8 TB | Produtos + Pedidos + Clientes (núcleo transacional) |
| NAS local | 50 TB | Imagens de produtos |
| Fitas magnéticas | ~200 TB | Logs históricos (compliance fiscal) |

O plano é faseado em 12 meses, migrando primeiro o que dá ROI rápido e baixo risco, deixando o núcleo transacional para uma janela com replicação online.

**a) Os 6 Rs por repositório**

| Repositório | R escolhido | Por quê |
|---|---|---|
| **Oracle 8 TB** | **Replatform** (com etapa inicial de Rehost para de-risk) | Sair de Oracle on-prem para banco gerenciado (HA, backup, patching automáticos). Oracle→Azure SQL é heterogêneo (muda o engine), há conversão de schema/PL-SQL. De-risk: subir o Oracle numa VM Azure primeiro (Rehost) e depois converter para o serviço gerenciado. |
| **NAS 50 TB (imagens)** | **Replatform** | Tirar arquivos de um NAS e colocá-los em Object Storage gerenciado (Blob): a aplicação deixa de apontar para `\\nas\...` e passa a usar URLs do Blob (servíveis por CDN). Pouca mudança de código, grande ganho de escala/custo. |
| **Fitas 200 TB (logs fiscais)** | **Retire + Replatform** (triagem) | Triar: o que já passou do prazo legal de retenção → Retire (descartar conforme política). O que ainda é exigido por fisco → Replatform para Blob Archive com imutabilidade (WORM). |

> Refactor puro (caro demais para 12 meses), Repurchase (sem SaaS que substitua o núcleo) e Retain (sem trava regulatória que obrigue ficar on-prem, desde que dados de brasileiros fiquem em região Brasil — item e) não são o caminho principal aqui.

**b) Serviço Azure de destino (custo × criticidade)**

| Repositório | Serviço Azure de destino | SKU/configuração | Racional |
|---|---|---|---|
| Núcleo transacional | **Azure SQL Managed Instance** (ou Azure SQL DB Business Critical) | Business Critical para Pedidos (alta criticidade, ACID); General Purpose para Produtos/Clientes | MI dá maior compatibilidade na vinda do Oracle e HA gerenciado. Pedidos = faturamento, não pode perder transação. |
| Imagens | **Blob Storage (Object)** | Hot para imagens recentes; lifecycle Hot→Cool→Archive para SKUs descontinuados | Servir via CDN, escala para 5M SKUs, custo por GB baixo. |
| Logs fiscais | **Blob Archive + immutability policy** | Archive tier, WORM (time-based retention), consulta via Synapse serverless | Mais barato da plataforma para "guardar e quase nunca ler"; imutabilidade satisfaz auditoria fiscal. |
| (Segredos das connection strings) | **Azure Key Vault** | RBAC, Managed Identity | As apps que migram não levam senha em config — lêem do Vault (ver 1.4). |

**c) Como migrar sem downtime**

A regra: migração online com replicação contínua + cutover curto no fim, nunca um "big bang".

- **Banco (8 TB):** Azure Database Migration Service (DMS) em modo online. Para Oracle→Azure SQL, usar SQL Server Migration Assistant (SSMA) para converter schema/código e DMS (ou Oracle GoldenGate para CDC) para replicação contínua. O on-prem segue produtivo enquanto o destino sincroniza; o cutover leva minutos, numa janela de baixo tráfego. Rollback garantido porque o Oracle continua intacto até a validação.
- **Imagens (50 TB):** seed inicial com Azure Data Box (50 TB via WAN levaria semanas). Depois, AzCopy faz o delta sync das imagens que mudaram durante o transporte. Cutover = repontar a aplicação para as URLs do Blob.
- **Logs em fita (200 TB):** processo offline em lote — não há "downtime" porque não é sistema vivo. Usar Data Box Heavy (~1 PB por dispositivo): fita → staging → Data Box → Blob Archive. É a fase mais longa do cronograma pelo volume.

**d) Estimativa de custo de egress dos 50 TB de imagens**

O ponto-chave: migrar *para* o Azure é **ingress**, e ingress é gratuito. Não existe custo de egress da Azure ao trazer as imagens de fora para dentro — o custo real de "tirar 50 TB do NAS" é banda/tempo de WAN ou o fee de um Data Box, não a tabela de egress da Azure.

Onde o egress da Azure realmente apareceria:

1. Se um dia a QC tirasse as imagens de volta para fora (saída p/ internet ou outra nuvem). 50 TB ≈ 51.200 GB; primeiros 100 GB/mês grátis; ~$0,087/GB (Brazil South → internet): `51.100 × $0,087 ≈ $4.446 (uma vez)`.
2. Egress recorrente de *servir* as imagens aos clientes — este sim é contínuo. Mitigação: Azure CDN/Front Door na frente do Blob, reduzindo egress de origem via cache nas bordas.

**Recomendação:** usar Data Box para o seed (paga-se o fee do dispositivo + frete, na casa de centenas de dólares, e zero egress/ingress) em vez de empurrar 50 TB pela internet — mais barato e mais rápido.

**e) Compliance LGPD — onde os dados de brasileiros podem ficar**

- **Residência de dados:** PII de clientes brasileiros fica em Brazil South (São Paulo), com Brazil Southeast como região par para DR/backup.
- **Controles obrigatórios:** criptografia em repouso (CMK no Key Vault) e em trânsito (TLS); RBAC de menor privilégio (1.4) + logs de auditoria; direitos do titular (soft-delete + purge no Blob, rotina de apagamento + pseudonimização no SQL/Cosmos); minimização (dados para BI/ML anonimizados/pseudonimizados).
- **Backups e fitas:** os backups e o histórico migrado também ficam em região Brasil.

**Cronograma resumido (12 meses)**

| Fase | Meses | Foco | R / Serviço |
|------|-------|------|-------------|
| 1 | 1–2 | Assessment, landing zone, Key Vault, redes, PoC | — |
| 2 | 2–4 | Imagens 50 TB → Blob (Data Box + AzCopy delta) | Replatform |
| 3 | 4–9 | Núcleo Oracle 8 TB → Azure SQL MI (SSMA + DMS online, cutover curto) | Replatform |
| 4 | 6–11 | Fitas 200 TB → triagem (Retire) + Blob Archive imutável (Data Box Heavy) | Retire + Replatform |
| 5 | 11–12 | Validação, hardening LGPD, descomissionamento do on-prem, FinOps | — |

---

### Exercício 2.3 — Particionamento no Cosmos DB

*Responsável: Tatiana Mastrogiovanni Haddad.*

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

## 🔴 Nível 3 — Bônus

*Responsável: Luciana Chaves D'Olivo — Exercícios 3.1 (vector search verdadeira), 3.2 (Synapse Serverless / query sobre Blob) e 3.3 (benchmark — script escrito, não testado).*

> Artefatos de código: `scripts/gerar_embeddings_vector.py` (3.1), `terraform/synapse.tf` + `scripts/gerar_logs_compras.py` (3.2). Instruções de execução no `README.md`.
>
> **Nota de honestidade:** sinalizamos claramente o que foi executado e o que não foi. O **3.1** rodou de verdade (vector search com `all-MiniLM-L6-v2`, resultados reais). O **3.2** tem a IaC real (`synapse.tf`, validada) e a demonstração do conceito no DuckDB, já que a subscription não permitiu provisionar o Synapse. O **3.3** tem o script completo (`benchmark_busca.py`), mas **não foi testado** — depende de SQL e Cosmos, bloqueados/indisponíveis na subscription. Não incluímos nenhum número que não tenhamos medido de fato.

### Exercício 3.1 — Vector search verdadeira no AI Search

Pra fazer vector search de verdade tivemos que subir o AI Search de Free para Basic — o tier Free não aceita campo vetorial (`Collection(Edm.Single)`). Criamos um índice `produtos-vector-index` com o campo `content_vector` (384 dimensões, HNSW, métrica de cosseno) e geramos os embeddings de "nome + descrição" dos 20 produtos com o `all-MiniLM-L6-v2` (via `sentence-transformers`). A mesma função de embedding é aplicada na pergunta do cliente — é exatamente o passo de retrieval que o agente da QC faz antes de montar o contexto pro Claude responder.

#### Parte A — Resultados das 3 queries

Rodamos o `all-MiniLM-L6-v2` sobre os 20 produtos do catálogo (embedding de "nome + descrição", normalizado) e medimos o cosseno entre cada pergunta e os produtos. O que mais nos chamou atenção foi o tanto que o modelo se atrapalha com português — em duas das três buscas ele errou feio.

**Query 1 — "preciso de uma cadeira boa para minha coluna"**

| # | Produto | Cosseno |
|---|---------|---------|
| 1 | Cadeira Gamer Vermelha | 0.540 |
| 2 | Cadeira Home Office Confortável | 0.538 |
| 3 | Camiseta Polo Masculina | 0.500 |

Ele entendeu que a gente queria uma cadeira e trouxe duas no topo, mas justamente a que resolveria o problema — a Cadeira Ergonômica DXRacer, a única do catálogo com "apoio lombar regulável" — ficou de fora do top-3. E ainda enfiou uma camiseta em terceiro, com score quase igual ao das cadeiras. Faltou o modelo ligar "coluna" a "apoio lombar"; essa ponte ele não fez.

**Query 2 — "algo para acompanhar séries"**

| # | Produto | Cosseno |
|---|---------|---------|
| 1 | Camiseta Polo Masculina | 0.397 |
| 2 | Mochila para Notebook 15.6 | 0.354 |
| 3 | Cafeteira Italiana 6 Xícaras | 0.318 |

Aqui ele se perdeu de vez. A Smart TV, que era a resposta óbvia, não apareceu nem no top-3 — vieram camiseta, mochila e cafeteira, nenhuma com qualquer relação, e com scores baixíssimos (0,32 a 0,40, sinal de que o próprio modelo estava "na dúvida"). "Acompanhar séries" não divide nenhuma palavra com o catálogo, e o modelo não tem o conhecimento de mundo, em português, pra associar série a uma televisão.

**Query 3 — "presente para um amigo que ama café"**

| # | Produto | Cosseno |
|---|---------|---------|
| 1 | Cafeteira Italiana 6 Xícaras | 0.534 |
| 2 | Cafeteira Nespresso Essenza Mini | 0.526 |
| 3 | Cadeira Gamer Vermelha | 0.370 |

Essa funcionou. As duas cafeteiras vieram em primeiro e segundo, bem destacadas — quando a palavra "café/cafeteira" aparece direto no produto, o modelo acerta sem sufoco. O terceiro lugar (cadeira gamer) já é ruído, com score bem mais baixo. A ideia de "presente" ninguém pegou, mas isso a gente nem esperava, já que não existe esse atributo no catálogo.

#### O que tiramos disso

Juntando as três, o padrão fica claro: o vector search só foi bem quando a pergunta tinha uma âncora forte de palavra (café → cafeteira). Quando dependia de entender uma paráfrase (coluna ≈ lombar) ou de conhecimento de mundo (séries → TV), o modelo ou perdeu o produto certo ou trouxe só ruído. Os scores baixos — quase tudo entre 0,32 e 0,54 — reforçam isso: não há uma separação semântica clara.

A lição não é "vector search não presta", e sim que o modelo faz toda a diferença. Com o all-MiniLM, o agente da QC erraria o primeiro resultado em duas de três perguntas — e errar o primeiro resultado estraga a resposta inteira, porque é esse produto que o agente usa pra responder. Pra valer em produção a gente trocaria por um modelo multilíngue de verdade (o `text-embedding-3-large`, da reflexão abaixo) e ainda colocaria uma busca por palavra-chave (BM25) por cima: pelo menos "cadeira" e "cafeteira" seriam pegos pelo termo exato, e o reranker reordenaria pelo que faz mais sentido.

Uma observação honesta sobre a execução: esses números saíram de rodar o modelo de verdade no catálogo (mesmo modelo e mesma conta de cosseno que o AI Search faz por baixo), depois de subir o `produtos.csv` pro Blob e provisionar o Storage e o AI Search Basic via Terraform. Não chegamos a rodar o semantic search do lab pra comparar lado a lado — então a comparação com keyword/semantic ficou no plano da discussão, não em números.

#### Parte B — Reflexão

**1. Por que `all-MiniLM-L6-v2` é má escolha para produção da QC?**
A própria Parte A já respondeu na prática. Primeiro, a **língua**: o modelo é treinado quase todo em inglês, e nossas queries e catálogo são em português — por isso ele errou "acompanhar séries" (nem trouxe a TV) e devolveu uma camiseta pra "cadeira pra coluna". Segundo, a **dimensionalidade**: 384 dimensões dão pouca resolução semântica perto das 3072 do `text-embedding-3-large`, e num catálogo de 5M de SKUs isso vira muito falso-positivo no topo, ou seja, o agente recebe contexto errado. E terceiro, **operação**: rodar o modelo na CPU serve pro lab, mas em produção a gente teria que hospedar e escalar isso (container/GPU, endpoint de ML), com toda a carga de versionamento e SLA que um serviço gerenciado já resolve.

**2. Que serviço Azure usar para embeddings em produção?**
**Azure OpenAI — `text-embedding-3-large`** (3072 dims), consumido como endpoint gerenciado. Vantagens: qualidade multilíngue (inclui PT-BR) muito superior, sem infra para manter, autenticação via **Managed Identity + Key Vault** (mesmo modelo de segredos da QC), e a opção de **reduzir dimensões** via parâmetro `dimensions` (ex.: 1536/1024) para baratear armazenamento no AI Search sem reindexar de modelo. O AI Search ainda permite ligar o embedding ao índice via **integrated vectorization** (skillset), eliminando código custom no caminho de ingestão.

**3. Como manter embeddings atualizados quando produtos novos chegam?**
Pipeline **incremental**, não reprocessamento total:
- **Gatilho por evento:** novo/alterado `produtos.csv` ou linha em `T_PRODUTOS` → **Event Grid / Azure Function** dispara só para o delta.
- **Idempotência por hash:** guardar um `content_hash` de `nome+descricao`; só re-embeddar se o hash mudou (evita custo e drift desnecessário).
- **Upsert no índice:** `mergeOrUpload` no AI Search por `id` (vetores novos sobrescrevem; demais ficam intactos).
- **Alternativa nativa:** **AI Search Indexer + skillset de integrated vectorization** com *change/high-water-mark detection* na fonte, rodando em schedule — embedding gerado dentro do próprio AI Search.
- **Governança:** ao **trocar a versão do modelo** de embedding, é preciso **reindexar tudo** (vetores de modelos diferentes não são comparáveis) — versionar o nome do modelo no índice e fazer cutover azul/verde.

**4. Custo de embeddings para 5M de produtos com Azure OpenAI**
Premissas: `text-embedding-3-large` a **US$ 0,13 / 1M tokens** (só input; embeddings não cobram output). **~50 tokens por produto** — coerente com `nome + descricao` curtos do catálogo da QC (ex.: *"Cadeira Ergonômica DXRacer. Cadeira de escritório com apoio lombar regulável e encosto de cabeça"* ≈ 30–40 tokens; arredondamos para 50 com folga, já que PT-BR tende a gerar mais tokens que EN).

```
Total de tokens = 5.000.000 produtos × 50 tokens = 250.000.000 tokens = 250 M tokens
Custo           = 250 M × (US$ 0,13 / 1 M)        = 250 × US$ 0,13
                = US$ 32,50  (carga inicial completa, one-shot)
```

| Cenário | Tokens | Custo |
|---------|--------|-------|
| Carga inicial 5M SKUs (50 tok/produto) | 250 M | **US$ 32,50** |
| Sensibilidade: 75 tok/produto | 375 M | US$ 48,75 |
| Manutenção mensal (~2% catálogo = 100k SKUs) | 5 M | US$ 0,65/mês |

> **Conclusão de custo:** o embedding **não é o gargalo financeiro** — a carga full dos 5M sai por ~US$ 32 (uma vez) e a manutenção incremental por centavos/mês. O custo relevante migra para **armazenamento vetorial e tier do AI Search** (5M × 3072 dims × 4 bytes ≈ **61 GB** de vetores, exigindo tier Standard com capacidade adequada). Daí a recomendação prática: usar `text-embedding-3-large` com `dimensions` reduzido (ex.: 1024) para cortar ~3× o storage do índice mantendo qualidade.

---

### Exercício 3.2 — Synapse Serverless: query sobre Blob

#### Setup (IaC, zero ETL)

A ideia central é **não mover dado**: os logs de compras da QC já moram no Blob/Lake; em vez de carregá-los num Dedicated DWH, apontamos o **Serverless SQL Pool** (motor "Built-in", gratuito em todo Synapse Workspace) diretamente para os arquivos via `OPENROWSET(BULK ...)`. Cobra-se por **TB processado na query**, não por cluster ligado.

O `terraform/synapse.tf` provisiona:

| Recurso | Papel |
|---|---|
| `azurerm_storage_account.lake` (`is_hns_enabled = true`) | Conta ADLS Gen2 **dedicada de analytics**, separada da `stqc...` transacional da Aula 2 |
| `azurerm_storage_data_lake_gen2_filesystem.synapse` | Filesystem que ancora o workspace |
| `azurerm_storage_data_lake_gen2_filesystem.logs` | Filesystem onde ficam os CSVs (`compras_*.csv`) |
| `azurerm_synapse_workspace.qc` | Workspace + Serverless; admin via `var.sql_admin_password` (sensitive), **nunca hardcoded** |
| `azurerm_synapse_firewall_rule.allow_azure` + `.cloud_shell` | Libera serviços Azure e o IP do Cloud Shell |
| `azurerm_role_assignment.synapse_lake_reader` | Managed Identity do workspace com `Storage Blob Data Reader` → lê o Lake **sem chave de conta** |

**Trade-off do HNS (`is_hns_enabled = true`):** o Synapse exige HNS (Hierarchical Namespace = ADLS Gen2) na conta primária. O HNS troca o *flat namespace* do Blob por uma **árvore real de diretórios**. Prós: rename/move/delete de pasta vira operação **atômica e O(1)** (essencial para particionar `logs/ano=YYYY/mes=MM/` e para o *partition pruning*), e ganha-se **ACLs POSIX** por diretório para governança do clickstream. Contras: **HNS é decidido na criação e não pode ser ligado depois** — a `stqc...` da Aula 2 nasceu *flat*, então não dá para "ativar" a flag nela; por isso provisionamos uma **conta de analytics dedicada** já com HNS. Há ainda leve sobrecusto de transações/metadados. Decisão arquitetural: **storage transacional (flat) ≠ data lake analítico (HNS)** desde o dia 1.

**Geração de dados:** `scripts/gerar_logs_compras.py` produz `logs_compras_jan.csv`, `_fev.csv`, `_mar.csv`, **1000 registros cada** (3000 total), datas distribuídas pelos dias de jan/fev/mar de 2026, colunas `pedido_id, periodo (DATE), cliente_id, categoria, uf, canal, qtd_itens, valor (DECIMAL)`. Seed fixa (reprodutível) e upload opcional via `DefaultAzureCredential` + `azure-storage-blob`.

**O que aconteceu no `terraform apply`:** o `synapse.tf` foi escrito e passa no `terraform validate`, mas não conseguimos subir o workspace nesta subscription de estudante. O workspace do Synapse é construído sobre um SQL Server, e a conta bloqueia a criação de SQL Server em qualquer região (`SqlServerRegionDoesNotAllowProvisioning`) — a mesma trava que nos impediu de usar o Azure SQL. Para não perder o aprendizado central (SQL serverless lendo arquivos direto, sem ETL, e o ganho do Parquet), rodamos a **mesma query** no **DuckDB** — um engine SQL serverless que lê CSV/Parquet direto, que é exatamente o conceito do `OPENROWSET` — sobre os mesmos CSVs. Os números abaixo são reais dessa execução.

#### A query

A intenção no Synapse Serverless:

```sql
SELECT CAST(periodo AS DATE) AS dia, COUNT(*) AS pedidos, SUM(valor) AS receita
FROM OPENROWSET(BULK 'https://STORAGE.blob.core.windows.net/logs/compras_*.csv',
  FORMAT='CSV', PARSER_VERSION='2.0', FIRSTROW=2)
  WITH (periodo VARCHAR(20), valor DECIMAL(10,2)) AS dados
GROUP BY CAST(periodo AS DATE) ORDER BY dia;
```

A mesma lógica que de fato rodamos, no DuckDB:

```sql
SELECT CAST(periodo AS DATE) AS dia, COUNT(*) AS pedidos, ROUND(SUM(valor),2) AS receita
FROM read_csv_auto('logs_compras_*.csv')
GROUP BY dia ORDER BY dia;
```

Nos dois, o `*` casa os 3 arquivos de uma vez e a query lê direto do storage, sem carregar nada num banco.

#### Resultados (reais — DuckDB sobre os 3 CSVs)

A query retornou **90 linhas** (um dia por linha, jan–mar/2026). Amostra:

| dia | pedidos | receita (R$) |
|---|---:|---:|
| 2026-01-01 | 26 | 90.737,35 |
| 2026-01-15 | 38 | 103.076,48 |
| 2026-01-31 | 34 | 75.285,97 |
| 2026-02-01 | 35 | 77.880,02 |
| 2026-02-14 | 42 | 129.015,06 |
| 2026-02-28 | 27 | 75.053,73 |
| 2026-03-01 | 37 | 66.546,57 |
| 2026-03-15 | 29 | 64.614,65 |
| 2026-03-31 | 42 | 136.273,18 |

**Totais por mês** (conferência): jan = 1000 pedidos / R$ 2.514.171,24 · fev = 1000 / R$ 2.514.616,93 · mar = 1000 / R$ 2.519.730,21. **Total: 3000 pedidos, R$ 7.548.518,38.**

#### CSV vs Parquet — medido de verdade

Os 3 CSVs somam **146.555 bytes** (~143 KiB). Convertendo os mesmos dados para **Parquet** (colunar, compressão Snappy) com o DuckDB, o arquivo cai para **51.417 bytes** (~50 KiB) — uma **redução real de 65%**, e isso só com a compressão. O ganho de verdade aparece na *query*: o Serverless cobra por **bytes lidos**, e a nossa usa só 2 das 8 colunas (`periodo`, `valor`). Em CSV (formato linha) não tem escapatória — pra somar `valor` o motor lê e parseia as 8 colunas inteiras. Em Parquet (colunar) ele lê **só as 2 colunas pedidas**, já comprimidas. Para 3 mil linhas a diferença é de KB; em **bilhões de linhas de clickstream da QC**, é a conta do mês: menos bytes lidos = menos TB faturado.

#### Reflexão

**1) Por que Serverless e não Dedicated Pool para a QC?**
Os logs de compras são uma carga **analítica intermitente e exploratória** (dashboards diários, análises ad hoc), não um DWH 24/7 com SLA de concorrência alta. O **Dedicated Pool** provisiona DWUs que **cobram por hora ligadas**, exige carga/ETL prévia (perde-se o "zero ETL") e fica caro ocioso. O **Serverless** não tem cluster: cobra **só por TB processado quando a query roda**, lê o Blob/Lake direto, escala sozinho e custa **R$ 0 quando ninguém consulta** — encaixe perfeito de **FinOps** para uma startup de e-commerce com volume crescente mas uso esporádico. Migra-se para Dedicated só quando houver workload **constante, previsível e com muitos usuários simultâneos**.

**2) Custo de 5 TB processados/mês a $5/TB:**

```
5 TB × $5/TB = $25/mês.
```

Vinte e cinco dólares para servir todas as queries analíticas de um mês inteiro — ordens de grandeza abaixo de um Dedicated Pool ligado.

**3) Como reduzir custo por query (Parquet + partições):**
O Serverless cobra por **bytes lidos**, então a meta é **ler menos bytes**:

- **Parquet (colunar + comprimido):** a query lê **só as colunas referenciadas** (`periodo`, `valor`), não as 8. Com compressão Snappy/ZSTD, os bytes despencam ~5–10× vs. CSV. Migrar os logs para Parquet pode levar os 5 TB para **~0,5–1 TB** → de **$25** para **~$2,50–$5/mês**.
- **Partições + partition pruning:** gravar particionado por data (`compras/ano=2026/mes=01/...`, viável e barato graças ao HNS) faz o motor **descartar pastas inteiras** que o filtro não toca. Uma query "março/2026" lê **só `mes=03/`**, ignorando ~⅔ dos arquivos.
- **Combinação:** **colunar (lê só as colunas) + pruning (lê só as partições)** ataca os dois eixos do volume varrido. É o padrão de **data lake analítico** da QC: Parquet particionado por data no ADLS Gen2, consultado por Serverless com custo previsível e mínimo.

> *Nota: o `synapse.tf` é a IaC real do exercício (escrita e validada com `terraform validate`); não foi possível provisionar o workspace nesta subscription por bloqueio de SQL Server. Os agregados e a comparação CSV/Parquet acima são de uma execução real no DuckDB sobre os CSVs do `gerar_logs_compras.py` — o mesmo conceito de SQL serverless sobre arquivos do Synapse `OPENROWSET`.*

---

### Exercício 3.3 — Benchmark: Cosmos vs SQL vs AI Search

> ⚠️ **Script entregue, mas não testado.** Implementamos o `scripts/benchmark_busca.py` com as três estratégias de busca para o produto "cadeira ergonômica para dor lombar" — Azure SQL com `LIKE`, Cosmos com `CONTAINS` e AI Search com vector search — medindo latência com `time.perf_counter()` (média + p95 sobre 10 queries, warm-up descartado). **Não conseguimos executá-lo:** ele depende de Azure SQL e Cosmos, e a subscription de estudante **não permite provisionar SQL Server** (`SqlServerRegionDoesNotAllowProvisioning`, a mesma trava do 3.2) nem disponibilizou Cosmos com capacidade. Por honestidade, **não incluímos números de latência ou custo que não medimos** — o script roda essa comparação assim que houver uma subscription com SQL e Cosmos disponíveis.

O que dá pra afirmar no campo conceitual (e que o 3.1 já mostrou na prática):

- **Azure SQL `LIKE`** e **Cosmos `CONTAINS`** são matching de substring literal — cegos a paráfrase ("coluna" não casa com "lombar"). Rápidos em latência bruta, mas péssimos em relevância. O Cosmos ainda não tem índice full-text nativo (`CONTAINS` é varredura, cara em RU/s), então na prática precisaria do AI Search **ao lado** dele.
- **AI Search vector** é o único que captura intenção — foi o que medimos de verdade no 3.1, onde justamente os casos de paráfrase derrubaram a busca literal.
- Para o agente de busca da QC (RAG), a escolha é **AI Search (vector + semantic ranker)** como tool primária, com **Azure SQL como filtro estrutural acoplado** (categoria, faixa de preço). Cada store fica no que faz melhor; SQL e Cosmos não competem com a busca semântica, complementam.

---

## Reflexão coletiva

Nesta aula compreendemos que **não devemos manter no código as chaves e secrets, não é uma questão de burocracia mas a fundação de qualquer plataforma agentic**. 

Na Aula 1 já tínhamos discutido IaC e reprodutibilidade e na aula 2 vimos que o Key Vault + Managed Identity complementam esse raciocínio: cada serviço (Function, AKS, agente de IA) recebe sua própria identidade gerenciada e acessa *apenas* o que precisa.

Secrets User lê, Secrets Officer administra, Reader audita. 
Isso não é apenas para evitar vazamento de senha no Git, mas para  **rastreabilidade e auditoria de quem (ou qual agente) acessou o quê**, o que no caso de múltiplos agentes autônomos operando sobre os mesmos dados sensíveis se torna tão essencial.

Essa lógica se conecta diretamente com a arquitetura de dados que desenhamos no Exercício 2.1: um agente conversacional da QC não é "um modelo respondendo perguntas", mas uma cadeia de serviços (AKS > Cosmos/SQL > AI Search > Azure OpenAI) onde cada elo precisa de credenciais próprias, escopadas e auditáveis. 
Sem Managed Identity, cada um desses elos seria um ponto de vazamento potencial. O particionamento do Cosmos (2.3) também reforça essa visão de "infraestrutura que escala com segurança": uma partição mal escolhida não é só um problema de performance, é um problema de **previsibilidade** e previsibilidade é exatamente o que um agente autônomo precisa para operar com confiança.

Se recomeçássemos o projeto QC hoje, definiríamos **Managed Identity e RBAC granular desde o primeiro Terraform aplicado** como parte do template-base de qualquer recurso novo (Function, AKS, Cosmos, AI Search). Também aplicaríamos lifecycle policies de Blob (Hot > Cool > Archive) desde o dia 1, já que o Exercício 1.2 mostrou que a diferença de custo composta ao longo de 5 anos é complexa.

Em resumo: segurança e FinOps são decisões de arquitetura que se tomadas tarde custam caro tanto em dinheiro quanto em retrabalho.

---

## Artefatos do ZIP

- Documento principal: `entrega-grupo-aula02.md` (este arquivo)
- Diagrama: `diagramas/arquitetura-qc-aula02.png`
- Código IaC (N3): `terraform/synapse.tf` (Synapse Serverless + ADLS Gen2 com HNS)
- Scripts (N3):
  - `scripts/gerar_embeddings_vector.py` — vector search verdadeira (Ex 3.1)
  - `scripts/gerar_logs_compras.py` — gera os CSVs de logs consultados no Ex 3.2
  - `scripts/benchmark_busca.py` — benchmark SQL × Cosmos × AI Search (Ex 3.3) — **escrito, não testado** (sem SQL/Cosmos na subscription)
- Instruções de execução: `README.md`
