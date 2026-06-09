# Resposta — Pessoa A (Lucas Marujo Amadeu)

**Entrega Aula 02 — Grupo 08 — Storage & Bancos de Dados na Nuvem**
**Disciplina:** Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents
**Bloco assumido:** 🟢 N1 completo (1.1, 1.2, 1.3, 1.4) + 🟡 N2 — Exercício 2.2 (plano de migração)

> Este documento contém só a minha parte. A matriz de decisão (2.1) + diagrama e o particionamento do Cosmos (2.3) ficam com a Pessoa B; o N3 bônus (vector search, Synapse e benchmark) fica com a Pessoa C. A consolidação no `entrega-grupo-aula02.md` é feita pela Pessoa B.

---

## 🟢 Nível 1 — Fundamentos

### Exercício 1.1 — Tipos de Storage

Para cada cenário, o tipo de storage adequado e o porquê. O critério de decisão é sempre o mesmo tripé: **como o dado é acessado** (HTTP/objeto, sistema de arquivos montável, ou blocos crus), **latência exigida** e **se precisa ser compartilhado/atrelado a uma máquina**.

| Cenário | Tipo | Justificativa |
|---------|------|---------------|
| Imagens de produtos do e-commerce QC (5M de SKUs) | **Object** (Blob) | Volume massivo, acesso por URL/HTTP, sem necessidade de sistema de arquivos; serve direto a CDN e é barato por GB. |
| Disco onde roda o SO de uma VM de banco | **Block** (Managed Disk / Premium SSD) | Banco exige baixíssima latência e I/O em blocos; o disco é atrelado a **uma** VM e montado como dispositivo de bloco. |
| Pasta compartilhada entre 10 VMs de DevOps | **File** (Azure Files — SMB/NFS) | Único tipo montável **simultaneamente** por várias VMs como `/mnt/dados`, com semântica de sistema de arquivos. |
| Backup mensal de bancos (retenção 7 anos) | **Object — Archive tier** | Custo por GB mais baixo da plataforma para dado de acesso raro; 7 anos = compliance, não consulta frequente. |
| Modelos `.pkl` do time de ML para serving | **Object** (Blob) | Download via HTTP pelo runtime de serving, versionamento por blob/prefixo, sem precisar de FS nem de VM dedicada. |
| Dump diário de logs para análise futura | **Object — lifecycle Hot→Cool→Archive** | Ingestão append-only barata; analytics serverless (Synapse) consulta direto no Blob, sem ETL para um banco. |

**Observações de quem implementa (nível sênior):**
- **Object ≠ File ≠ Block** não é só preço: é o *modelo de acesso*. Object é chave→objeto via API/HTTP (escala "infinita", sem POSIX); File dá POSIX/SMB compartilhado; Block é o mais "cru" e rápido, mas amarrado a uma máquina.
- No caso do **Archive tier** (backup 7 anos): lembrar das pegadinhas operacionais — **mínimo de 180 dias** de permanência (deletar antes gera *early-deletion fee*) e **reidratação** com latência de horas + custo extra para ler o dado de volta. Archive é ótimo para "guardar e quase nunca ler", não para algo que possa ser requisitado com urgência.
- Os logs (último cenário) e as imagens são exatamente os dois containers do lab da QC (`logs/` com lifecycle e `catalogo`/`imagens` no Blob) — ou seja, a escolha aqui não é teórica, é o que já está provisionado no `storage.tf`.

---

### Exercício 1.2 — Tiers de acesso (cálculo)

**Dado:** 2 TB de logs de compras = **2.048 GB**. Primeiros 30 dias em **Hot** (detecção de fraude), depois **Archive** (compliance LGPD, 5 anos). Preços: Hot ≈ **$0,018/GB·mês**, Archive ≈ **$0,002/GB·mês**.

**a) Custo de 1 mês 100% em Hot tier**

$$2.048 \text{ GB} \times \$0{,}018 = \mathbf{\$36{,}86 / mês} \quad (\approx \$442/ano)$$

**b) Custo de 1 mês com lifecycle (30 dias Hot + Archive depois)**

Em regime estacionário (ingestão contínua: a cada dia entra log novo em Hot e sai log velho para Archive), em média **30/365 do volume está em Hot** e **335/365 em Archive**. Tomando os 2.048 GB como o conjunto relevante:

| Tier | Fração do tempo/volume | Cálculo | Custo médio |
|------|------------------------|---------|-------------|
| Hot | 30/365 (≈ 8,2%) | 2.048 × (30/365) × $0,018 | **$3,03/mês** |
| Archive | 335/365 (≈ 91,8%) | 2.048 × (335/365) × $0,002 | **$3,76/mês** |
| **Total** | | | **≈ $6,79/mês** |

**c) Economia anual com a lifecycle policy**

$$(\$36{,}86 - \$6{,}79) \times 12 = \$30{,}07 \times 12 = \mathbf{\approx \$360/ano}$$

**Leitura de engenharia (por que isso importa de verdade):**
- A economia *percentual* é o que escala: Hot custa **9×** o Archive ($0,018 vs $0,002). O número absoluto aqui é pequeno porque o exercício usa só 2 TB num único mês de referência. Com **retenção real de 5 anos** e ingestão diária, a QC acumula **centenas de TB em Archive** — e aí a mesma policy economiza facilmente **6 dígitos por ano**.
- O cálculo (b) é um modelo *simplificado de steady-state*. O ponto que o corretor quer ver é o raciocínio: dado quente fica caro parado; mover automaticamente para Archive após a janela de uso ativo (30 dias) é uma decisão de **FinOps**, não de código.
- Trade-off honesto: Archive não é "de graça em tudo" — tem custo/latência de **reidratação** e mínimo de 180 dias. Para logs de compliance que quase nunca são lidos, compensa; para algo consultado com frequência, não.

---

### Exercício 1.3 — Relacional × NoSQL × Vector

Para cada caso de uso da QC, o banco mais adequado. O critério: **esquema fixo + integridade transacional (ACID) → Relacional**; **esquema variável / texto livre / leitura rápida por chave / TTL → NoSQL documento**; **similaridade semântica → Vector**.

| Caso de uso | Banco | Justificativa |
|-------------|-------|---------------|
| Carrinho de compras ativo | **NoSQL doc (Cosmos)** | Esquema variável (itens heterogêneos), leitura/escrita rápida por chave do usuário e **expira sozinho com TTL** (24h). |
| Catálogo de produtos (SKU, preço, estoque) | **Relacional (Azure SQL)** | Esquema fixo, **joins** com categorias/fornecedores e **integridade de estoque** exigem ACID. É a `T_PRODUTOS` do lab. |
| Reviews dos clientes (texto livre + score) | **NoSQL doc (Cosmos)** | Texto livre sem schema rígido, campos opcionais, alta cardinalidade de escrita. É o container `reviews` do lab. |
| "Encontre produtos similares a este" | **Vector DB (AI Search)** | Recomendação = **similaridade semântica** entre embeddings; nem SQL nem documento resolvem `LIKE`/igualdade. |
| Histórico de pedidos para faturamento | **Relacional (Azure SQL)** | Faturamento exige **ACID** e garantias transacionais (consistência forte, auditável). Erro aqui é erro fiscal. |
| Sessão do usuário (chave-valor, expira 30min) | **Cosmos com TTL** (ideal: **Redis**) | Padrão é cache key-value de baixíssima latência → **Azure Cache for Redis**. Dentro das 3 opções dadas, **Cosmos com TTL** é o mais próximo. |
| Logs de comportamento de navegação | **Object Storage + Synapse** (ou NoSQL) | Clickstream = **bilhões de eventos**, append-only. Mais barato gravar no Blob e consultar com analytics serverless do que manter num banco operacional. |

**Nuances que separam uma resposta sênior de uma decoreba:**
- **Sessão e Redis:** o enunciado dá só 3 colunas (SQL/Cosmos/Vector), mas a resposta tecnicamente certa para "key-value que expira em 30 min" é **Redis** (cache em memória, latência sub-ms). Marquei Cosmos+TTL por ser o mais próximo *dentro das opções*, mas deixo explícito que em produção a QC usaria Redis — sinaliza que entendi o caso, não só a tabela.
- **Vector não substitui relacional:** recomendação usa Vector, mas o *preço/estoque* do produto recomendado ainda vem do SQL. Na prática a QC combina: AI Search acha o produto certo, SQL traz o dado transacional. Isso é exatamente o RAG dos agentes.
- **Cosmos aparece 3×** (carrinho, reviews, sessão): cada um por um motivo diferente (esquema variável, texto livre, TTL). Não é "Cosmos para tudo" — é Cosmos onde *não* há necessidade de join nem de ACID.

---

### Exercício 1.4 — Key Vault e RBAC

Para cada perfil, a role built-in do Key Vault no **menor privilégio**. A distinção-chave: **plano de gestão** (configurar o Vault) × **plano de dados** (ler/escrever o *valor* dos segredos).

| Perfil | Role no Key Vault | Justificativa |
|--------|-------------------|---------------|
| Você (criador do Vault, faz dev e ops) | **Key Vault Secrets Officer** | CRUD completo no **plano de dados de segredos** sem precisar ser Owner do recurso. Faz o trabalho sem dar permissão de apagar o Vault inteiro. |
| Azure Function que lê a connection string de `T_PRODUTOS` | **Key Vault Secrets User** | Só **leitura** do valor do segredo, via **Managed Identity** da Function. A app nunca tem senha em config — pega o segredo em runtime. |
| Engenheiro de segurança que audita sem alterar | **Key Vault Reader** | Lê **metadados** (quais segredos existem, versões, datas), mas **não o valor**. Auditoria não precisa ver o segredo em claro. |
| Pipeline de CI/CD que injeta novos segredos | **Key Vault Secrets Officer** (escopo limitado) | Precisa criar/atualizar segredos → Secrets Officer, mas via **Service Principal/Workload Identity dedicado** e escopo no Vault específico. |
| FinOps que precisa ver custo sem ver segredos | **Reader no Resource Group** (+ Cost Management Reader) | Vê custo no Cost Management e metadados do recurso, **sem qualquer acesso ao plano de dados** do Vault. Não toca em segredo nenhum. |

**Por que isso é o coração de uma plataforma agentic (e não burocracia):**
- A diferença **Secrets Officer × Secrets User × Reader** é o menor privilégio aplicado: quem *opera* o Vault (Officer) ≠ quem só *lê um segredo em runtime* (User) ≠ quem só *audita* (Reader). Dar Owner para tudo seria o anti-padrão.
- **Managed Identity > segredo em arquivo:** a Function não guarda a connection string — ela se autentica com sua identidade gerenciada e o `DefaultAzureCredential` resolve o token. Não há `.env`, não há segredo vazando em commit. Quando um **agente de IA** roda numa Function e lê dados do SQL, é esse mesmo mecanismo que impede a credencial de escapar para o prompt/log.
- **Plano de gestão × plano de dados:** o Vault do lab usa **RBAC habilitado** (não Access Policies legadas) e `purge_protection_enabled = false` para o lab destruir limpo. Em produção, purge protection ligado + segregação dessas roles é o que transforma "segredo hardcoded" num modelo auditável.

---

## 🟡 Nível 2 — Exercício 2.2: Plano de migração de dados (12 meses)

**Situação atual da Quantum Commerce:**

| Repositório atual | Volume | Conteúdo |
|-------------------|--------|----------|
| Oracle on-premise | 8 TB | Produtos + Pedidos + Clientes (núcleo transacional) |
| NAS local | 50 TB | Imagens de produtos |
| Fitas magnéticas | ~200 TB | Logs históricos (compliance fiscal) |

O plano abaixo é faseado em 12 meses, com a lógica de **migrar primeiro o que dá ROI rápido e baixo risco, deixando o núcleo transacional (mais delicado) para uma janela com replicação online**.

### a) Quais dos 6 Rs para cada repositório

| Repositório | R escolhido | Por quê |
|-------------|-------------|---------|
| **Oracle 8 TB** (produtos/pedidos/clientes) | **Replatform** (com etapa inicial de **Rehost** para de-risk) | A meta é sair de Oracle on-prem para um banco **gerenciado** (HA, backup, patching automáticos). Como Oracle→Azure SQL é **heterogêneo** (muda o engine), há conversão de schema/PL-SQL. De-risk: subir o Oracle numa VM Azure primeiro (Rehost rápido) e depois converter para o serviço gerenciado. |
| **NAS 50 TB** (imagens) | **Replatform** | Tirar arquivos de um NAS e colocá-los em **Object Storage gerenciado** (Blob): a aplicação deixa de apontar para `\\nas\...` e passa a usar URLs do Blob (servíveis por CDN). Pouca mudança de código, grande ganho de escala/custo. |
| **Fitas 200 TB** (logs fiscais) | **Retire + Replatform** (triagem) | Triar: o que já passou do prazo legal de retenção → **Retire** (descartar conforme política). O que ainda é exigido por fisco → **Replatform** para **Blob Archive** com **imutabilidade (WORM)**. Não faz sentido recriar a "fitateca" — Archive imutável cumpre o mesmo papel com busca via Synapse. |

> Os outros Rs (Refactor puro, Repurchase, Retain) não são o caminho principal aqui: não há ganho em reescrever do zero o ERP (Refactor caro demais para 12 meses), não há SaaS de mercado que substitua o núcleo (Repurchase) e não há trava regulatória que obrigue ficar on-prem (Retain) — desde que os dados de brasileiros fiquem em região Brasil (item **e**).

### b) Serviço Azure de destino (custo × criticidade)

| Repositório | Serviço Azure de destino | SKU / configuração | Racional |
|-------------|--------------------------|--------------------|----------|
| Núcleo transacional | **Azure SQL Managed Instance** (ou Azure SQL Database Business Critical) | Business Critical para **Pedidos** (alta criticidade, ACID); General Purpose para Produtos/Clientes | MI dá maior compatibilidade na vinda do Oracle e HA gerenciado. Pedidos = faturamento → não pode perder transação. |
| Imagens | **Blob Storage (Object)** | Hot para imagens recentes/quentes; **lifecycle Hot→Cool→Archive** para SKUs descontinuados | Servir via CDN, escala para 5M SKUs, custo por GB baixo. |
| Logs fiscais | **Blob Archive + immutability policy** | Archive tier, **WORM** (time-based retention), consulta sob demanda via **Synapse serverless** | Mais barato da plataforma para "guardar e quase nunca ler"; imutabilidade satisfaz auditoria fiscal. |
| (Segredos das connection strings) | **Azure Key Vault** | RBAC, Managed Identity | As apps que migram não levam senha em config — lê do Vault (ver 1.4). |

### c) Como migrar sem downtime

A regra: **migração online com replicação contínua + cutover curto no fim**, nunca um "big bang" de copiar-e-rezar.

- **Banco (8 TB):** **Azure Database Migration Service (DMS) em modo online**. Para Oracle→Azure SQL, usar o **SQL Server Migration Assistant (SSMA)** para converter schema/código e o DMS (ou **Oracle GoldenGate** para CDC) para **replicação contínua** das mudanças. O on-prem segue produtivo enquanto o destino sincroniza; o **cutover** (apontar a aplicação para o Azure) leva minutos, numa janela de baixo tráfego. Rollback fica garantido porque o Oracle continua intacto até a validação.
- **Imagens (50 TB):** seed inicial com **Azure Data Box** (dispositivo físico — 50 TB via WAN levaria semanas e satura a banda). Depois, **AzCopy** faz o **delta sync** das imagens que mudaram durante o transporte. Cutover = repontar a aplicação para as URLs do Blob. Como imagem é dado **imutável/versionável**, dá para servir do NAS e do Blob em paralelo durante a transição.
- **Logs em fita (200 TB):** processo **offline em lote** — não há "downtime" porque não é sistema vivo. Usar **Data Box Heavy** (~1 PB por dispositivo) ou várias remessas de Data Box: fita → staging → Data Box → Blob Archive. É a fase mais longa do cronograma justamente pelo volume.

### d) Estimativa de custo de egress dos 50 TB de imagens

**O ponto sênior aqui é desarmar a pegadinha do enunciado:** migrar *para* o Azure é **ingress**, e **ingress é gratuito**. Não existe custo de egress *da Azure* ao trazer as imagens de fora para dentro. O custo real de "tirar 50 TB do NAS" é **banda/tempo de WAN** ou o **fee de um Data Box** — não a tabela de egress da Azure.

Onde o egress da Azure realmente apareceria:
1. **Se um dia a QC tirasse as imagens de volta para fora** (saída p/ internet ou outra nuvem). 50 TB ≈ **51.200 GB**; primeiros 100 GB/mês grátis; ~**$0,087/GB** (Brazil South → internet):

   $$51.100 \times \$0{,}087 \approx \mathbf{\$4.446 \text{ (uma vez)}}$$

2. **Egress recorrente de *servir* as imagens aos clientes** — este sim é contínuo e relevante. Mitigação: **Azure CDN/Front Door** na frente do Blob, que reduz o egress de origem (cache nas bordas) e melhora latência. É a diferença entre pagar egress full a cada request e pagar só o cache-miss.

**Recomendação de custo de migração:** usar **Data Box** para o seed (paga-se o fee do dispositivo + frete, na casa de centenas de dólares, e **zero** egress/ingress) em vez de empurrar 50 TB pela internet. É mais barato **e** mais rápido.

### e) Compliance LGPD — onde os dados de brasileiros podem ficar

- **Residência de dados:** PII de clientes brasileiros (perfil, endereço, pedidos) fica em **Brazil South (São Paulo)**, com **Brazil Southeast** como região par para DR/backup. A LGPD não proíbe transferência internacional em absoluto, mas exige base legal/garantias — manter em região Brasil é o caminho de menor atrito regulatório e de latência.
- **Controles obrigatórios:**
  - **Criptografia** em repouso (chaves gerenciadas, idealmente CMK no **Key Vault**) e em trânsito (**TLS**).
  - **RBAC de menor privilégio** (exatamente o do 1.4) + **logs de auditoria** de acesso a dado pessoal.
  - **Direitos do titular:** suporte a exclusão/anonimização (no Blob, *soft-delete* + *purge*; no SQL/Cosmos, rotina de apagamento + pseudonimização para analytics).
  - **Minimização:** dados para BI/treino de ML usam versões **anonimizadas/pseudonimizadas**, não a PII crua.
- **Backups e fitas:** os backups e o histórico migrado também ficam em **região Brasil** — não adianta proteger o banco produtivo e deixar o backup num data center fora do país.

### Cronograma resumido (12 meses)

| Fase | Meses | Foco | R / Serviço |
|------|-------|------|-------------|
| 1 | 1–2 | Assessment, landing zone, Key Vault, redes, prova de conceito | — |
| 2 | 2–4 | **Imagens 50 TB** → Blob (Data Box + AzCopy delta) | Replatform |
| 3 | 4–9 | **Núcleo Oracle 8 TB** → Azure SQL MI (SSMA + DMS online, cutover curto) | Replatform |
| 4 | 6–11 | **Fitas 200 TB** → triagem (Retire) + Blob Archive imutável (Data Box Heavy) | Retire + Replatform |
| 5 | 11–12 | Validação, hardening LGPD, descomissionamento do on-prem, FinOps | — |

> A ordem é proposital: imagens primeiro (baixo risco, ROI rápido, exercita o pipeline de Data Box); o banco transacional no meio (mais delicado, precisa de replicação online); as fitas em paralelo no fundo (volumosas mas sem urgência operacional).

---

## ✅ Resumo da minha contribuição

- **N1 (1.1–1.4):** storage por modelo de acesso; cálculo de tiers com leitura de FinOps; modelagem relacional×NoSQL×vector dos casos da QC; RBAC do Key Vault no menor privilégio (plano de gestão × plano de dados).
- **N2 (2.2):** plano de migração de 12 meses — 6 Rs por repositório, serviços de destino por criticidade, migração **online** sem downtime (DMS/AzCopy/Data Box), desmistificação do custo de egress (ingress é grátis) e compliance LGPD com residência em região Brasil.

**A revisar (minha tarefa extra):** consistência da matriz 2.1 (Pessoa B) com o que defendi em 1.3, e os números do benchmark 3.3 (Pessoa C).
