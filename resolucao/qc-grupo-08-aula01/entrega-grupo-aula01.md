# Entrega Aula 01 — Grupo 08

**Disciplina:** Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents
**Turma:** 1AIER
**Data de entrega:** <07/06/2026>

## Grupo

| # | Nome completo                 | GitHub                         | E-mail FIAP          |
|---|-------------------------------|--------------------------------|----------------------|
| 1 | Tatiana Mastrogiovanni Haddad | https://github.com/TatiHaddad  | rm373809@fiap.com.br |
| 2 | Luciana Chaves D'Olivo        | https://github.com/l-cdolivo   | rm371277@fiap.com.br |
| 3 | Lucas Marujo Amadeu           | https://github.com/lucasmarujo | rm370469@fiap.com.br |

## Distribuição do trabalho

| Membro                 | Nível assumido         | Item específico                                                               |
|------------------------|------------------------|-------------------------------------------------------------------------------|
| Tatiana Mastrogiovanni | 🟢 N1 + 🔴 N3 (bônus) | Exercícios 1.1, 1.2, 1.3, 1.4 + 3.3 (multi-cloud)                             |
| Luciana Chaves D'Olivo | 🟡 N2 + coordenação   | Exercício 2.1 (arquitetura + diagrama) + 2.3; montagem do doc, reflexão e ZIP |
| Lucas Marujo Amadeu    | 🟡 N2 + 🔴 N3 (bônus) | Exercício 2.2 (custos) + 3.1 (Terraform) + 3.2 (Bicep)                        |

---

## 🟢 Nível 1 — Respostas

*Responsável: Tatiana Mastrogiovanni — Exercícios 1.1, 1.2, 1.3, 1.4.*

### Exercício 1.1 — Mapeamento de modelos de serviço

| Serviço                              | Modelo | Justificativa                                                                                                               |
|--------------------------------------|--------|-----------------------------------------------------------------------------------------------------------------------------|
| Gmail                                | SaaS   | Aplicação completa entregue via browser, onde o usuário não gerencia nenhuma camada de infraestrutura ou plataforma.        |
| Azure Virtual Machines               | IaaS   | O usuário provisiona e gerencia o Sistema Operacional, rede e armazenamento. A Microsoft fornece apenas o hardware virtualizado. |
| Azure App Service (hospedar uma API) | PaaS   | O desenvolvedor faz o deploy do código e a plataforma cuida do Sistema Operacional, runtime, escalonamento e patches.       |
| AWS Lambda                           | FaaS   | Execução de funções sob demanda sem necessidade de gerenciar servidor. Cobrança realizada por invocações e tempo de execução. |
| Azure SQL Database                   | PaaS   | Banco de dados gerenciado: o usuário administra esquemas e dados, e a Microsoft cuida do Sistema Operacional, backup e HA.  |
| Salesforce CRM                       | SaaS   | CRM completo entregue como serviço. Personalização via configuração e não via infraestrutura.                              |
| Google Kubernetes Engine (GKE)       | PaaS   | O control plane do K8s é gerenciado pelo Google; o usuário gerencia os workloads e os nós, com elementos de IaaS nos worker nodes. |
| Azure Blob Storage                   | IaaS   | Armazenamento de objetos de baixo nível gerenciado pelo usuário; não há camada de aplicação sobre o dado.                   |
| Azure OpenAI Service                 | PaaS   | API gerenciada de modelos de IA. O usuário consome endpoints sem gerenciar modelos, GPUs ou infraestrutura subjacente.      |

### Exercício 1.2 — Os 6 Rs na prática

**Cenário A — Sistema de rastreamento de frotas (código de 2008, sem documentação):**
**R escolhido: Rehost (Lift & Shift).** O sistema possui código legado de 2008 e o objetivo é migrar rápido para ganhar elasticidade com o menor risco possível. Como não há documentação e apenas uma pessoa conhece o sistema, qualquer refatoração eleva o risco significativamente. O Rehost move a VM para a nuvem sem alteração de código, entregando elasticidade e resiliência com prazo e risco mínimos.

**Cenário B — ERP de RH local (menos de 5 usuários/mês):**
**R escolhido: Retire.** O uso é insignificante. Manter a infraestrutura tem custo operacional e de segurança sem retorno proporcional. A ação correta é descontinuar o sistema, arquivar os dados conforme a política de retenção e redirecionar os poucos usuários para outra solução.

**Cenário C — API de pagamentos monolítica:**
**R escolhido: Refactor (Re-architect).** A fintech já decidiu aproveitar a migração para reestruturar a aplicação em microserviços com K8s e event-driven. A reescrita parcial da arquitetura caracteriza a refatoração, com ganho de escalabilidade independente por serviço e maior resiliência a falhas.

**Cenário D — CRM interno de 15 anos:**
**R escolhido: Repurchase.** O SaaS de mercado atende quase a totalidade das necessidades por custo menor, então substituir o sistema proprietário é a decisão economicamente racional — eliminando dívida técnica e liberando o time para atividades de maior valor.

**Cenário E — Mainframe com dados que devem ficar on-premise por exigência do BACEN:**
**R escolhido: Retain.** O requisito regulatório explícito impede a migração. O sistema permanece on-premise até que a regulação seja revisada ou a instituição obtenha autorização específica. Migrar sem cumprir os requisitos regulatórios geraria problema grave de compliance.

### Exercício 1.3 — Calculando o impacto do SLA

Sistema de e-commerce com SLA de 99,9%.

**a) Horas de downtime por ano:** **8,76 horas/ano**
> Downtime anual = 8.760 × (1 − SLA/100) = 8.760 × (1 − 99,9/100) = 8.760 × 0,001 = **8,76 h/ano**

**b) Impacto financeiro máximo por ano (R$ 50.000/hora):** **R$ 438.000/ano**
> Impacto = R$ 50.000/h × 8,76 h = **R$ 438.000**

**c) SLA mínimo para impacto < R$ 50.000/ano:** **≈ 99,99%**
> Para impacto < R$ 50.000, no máximo 1 h de downtime/ano: 1 ÷ 8.760 = 0,0001142 → SLA = 1 − 0,0001142 = 0,9998858 = **99,9886%** → na prática, **SLA 99,99%**.

### Exercício 1.4 — RBAC na prática

| Perfil                                                             | Role Azure mais adequada      | Justificativa                                                                                                                  |
|--------------------------------------------------------------------|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| Agente de IA que LÊ produtos do Storage para responder ao cliente  | Storage Blob Data Reader      | Permissão mínima de leitura em Blob Storage. O agente não precisa escrever nem gerenciar recursos — princípio do menor privilégio. |
| Engenheiro de dados que CARREGA novos catálogos no Blob            | Storage Blob Data Contributor | Precisa de leitura e escrita em Blob. Escopo restrito ao storage, evitando acesso a outros recursos da assinatura.            |
| Time de FinOps que precisa VER custos sem alterar recursos         | Cost Management Reader        | Acesso somente de leitura ao Cost Management. Não confere permissão sobre recursos de computação ou dados.                    |
| Auditor externo que precisa LER configurações de toda a assinatura | Reader (na assinatura)        | Leitura em todos os recursos sem possibilidade de alteração. Escopo de assinatura garante a visibilidade ampla da auditoria. |
| Sistema de CI/CD que provisiona infraestrutura via Terraform       | Contributor (no Resource Group) | Precisa criar/modificar recursos. Limitar ao Resource Group específico reduz o raio de impacto (blast radius) em caso de comprometimento do service principal. |

---

## 🟡 Nível 2 — Respostas + Implementação

### Exercício 2.1 — Arquitetura de alto nível: Quantum Commerce

*Responsável: Luciana Chaves D'Olivo.*

**Contexto:** QC = e-commerce em 12 países, 5M de SKUs, buscando experiência de compra com **IA conversacional**. A arquitetura precisa suportar agentes conversacionais com **base vetorial** (RAG sobre o catálogo) e **APIs serverless** — a contribuição desta disciplina para o case.

#### 1. Camadas da arquitetura

Propomos **6 camadas**, do usuário até a operação:

| # | Camada | O que faz | Por que existe na QC |
|---|--------|-----------|----------------------|
| 1 | **Edge / Entrega** | CDN, WAF e DNS global; serve frontend e imagens de produto perto do usuário | 12 países → latência e cache de imagens de 5M SKUs são críticos |
| 2 | **Frontend / Experiência** | Web/app + a interface do **chat conversacional** | É o ponto de contato com o cliente |
| 3 | **API / Orquestração** | APIs serverless (HTTP) + **orquestração do agente**: recebe a pergunta, decide ferramentas, chama IA e dados | Coração do projeto: serverless escala com o tráfego sazonal do varejo |
| 4 | **Dados** | Catálogo (NoSQL, para lidar com as diferentes características de produtos), pedidos/clientes (relacional), imagens (Blob Storage) e a **base vetorial** (embeddings do catálogo para RAG) | O agente só responde bem se recupera o produto certo |
| 5 | **IA / Cognitiva** | LLM conversacional, busca semântica e serviços cognitivos (visão para busca por imagem, sentimento de reviews) | É o que transforma a QC de e-commerce em e-commerce **agentic** |
| 6 | **Observabilidade & Segurança** | Logs, métricas, tracing, gestão de identidade e segredos (Key Vault) | Agente em produção precisa ser auditável, seguro e rastreável (custo de token, alucinação, abuso) |

**Como as camadas conversam (fluxo de uma pergunta do cliente):**
`Cliente → (1) CDN/WAF → (2) Frontend/Chat → (3) API serverless + Orquestrador do agente → (5) LLM`. Antes de responder, o orquestrador faz **(4) busca vetorial** no catálogo (RAG) e consulta os bancos relacional/NoSQL para preço e estoque; a camada **(6)** de observabilidade e identidade permeia todas as demais.

#### 2. Provedor principal — **Azure**

Escolhemos **Azure** como nuvem principal da QC, por quatro motivos:

1. **IA conversacional madura e gerenciada** — **Azure OpenAI / AI Foundry** entrega os modelos de LLM com SLA corporativo, cota dedicada e isolamento de rede, exatamente o núcleo do case. É o diferencial mais forte para a QC.
2. **Vector DB nativo** — **Azure AI Search** já tem busca vetorial + híbrida integrada, encurtando a camada de RAG sem montar um vetor DB separado.
3. **Identidade e segurança first-class** — Entra ID + Managed Identity + RBAC granular (mapeado no Ex. 1.4) reduzem segredos no código e o esforço operacional.
4. **Compliance e região** — a disponibilidade de **Brazil South** ajuda na LGPD para dados de clientes brasileiros, e o ecossistema Azure (Bicep, Azure Policy) está alinhado aos labs da disciplina.


#### 3. Serviços por categoria

| Categoria | Serviço Azure | Alternativa AWS | Alternativa GCP |
|-----------|--------------|-----------------|-----------------|
| Compute (backend) | Azure Functions + Container Apps | AWS Lambda + ECS/Fargate | Cloud Functions + Cloud Run |
| Storage (catálogo, imagens) | Azure Blob Storage | Amazon S3 | Cloud Storage |
| Banco relacional | Azure Database for PostgreSQL (Flexible Server) | Amazon RDS for PostgreSQL / Aurora | Cloud SQL for PostgreSQL / AlloyDB |
| Banco NoSQL | Azure Cosmos DB | Amazon DynamoDB | Firestore / Bigtable |
| Vector Database | Azure AI Search (busca vetorial) | Amazon OpenSearch Serverless (vetorial) | Vertex AI Vector Search |
| Serviços de IA cognitivos | Azure OpenAI + Azure AI Services (Vision, Language) | Amazon Bedrock + Rekognition/Comprehend | Vertex AI + Vision/Natural Language API |
| CDN | Azure Front Door / Azure CDN | Amazon CloudFront | Cloud CDN |
| Mensageria/Filas | Azure Service Bus / Event Grid | Amazon SQS / SNS / EventBridge | Pub/Sub |
| Observabilidade (logs/métricas) | Azure Monitor + Application Insights | Amazon CloudWatch + X-Ray | Cloud Monitoring + Cloud Trace |

#### 4. Diagrama

> Diagrama completo em **`diagramas/arquitetura-qc-aula01.png`**. 

---

### Exercício 2.2 — Comparativo de custos (3 provedores)

*Responsável: Lucas Marujo Amadeu.*

#### Premissas

Preços de tabela **on-demand** consultados nas páginas oficiais (jun/2026), Linux, em USD, regiões **Azure East US / AWS us-east-1 / GCP us-central1**. Base de **730 horas/mês**. Recalcular nas calculadoras oficiais antes do envio (preço de nuvem muda com frequência).

- **Compute:** instância _general purpose_ 2 vCPU / 8 GB, 24/7.
- **Storage:** 500 GB de _object storage_ padrão/quente, redundância local (LRS/regional).
- **Banco:** PostgreSQL **gerenciado**, 2 vCPU / 8 GB + 100 GB, **zonal / single-AZ** (sem HA).
- **Serverless:** 10 milhões de execuções/mês, **512 MB**, **~200 ms** (= 1.000.000 GB-segundos), sem abater a camada gratuita.

#### Memória de cálculo (taxas unitárias)

| Recurso | Azure | AWS | GCP |
|---------|-------|-----|-----|
| VM 2vCPU/8GB (US$/h) | D2s_v3 — **0,096** | m5.large — **0,096** | e2-standard-2 — **0,067** |
| Object storage (US$/GB-mês) | Blob Hot LRS — **0,018** | S3 Standard — **0,023** | Cloud Storage Standard — **0,020** |
| Banco — compute | PG Flexible GP 2vCore ≈ **0,144/h** | RDS db.m5.large — **0,192/h** | Cloud SQL: **0,0413/vCPU-h + 0,007/GB-h** |
| Banco — storage (US$/GB-mês) | **0,115** | gp3 — **0,115** | SSD — **0,17** |
| Serverless | exec **0,20/M** + **0,000016**/GB-s | exec **0,20/M** + **0,00001667**/GB-s | exec **0,40/M** (2M grátis) + CPU/mem |

#### Tabela comparativa (totais)

| Item | Azure | AWS | GCP | Tipo / cálculo |
|------|-------|-----|-----|----------------|
| 2 × VM (2 vCPU / 8 GB) | US$ 140 | US$ 140 | US$ 98 | `0,096×730×2` · `0,096×730×2` · `0,067×730×2` |
| 500 GB object storage | US$ 9 | US$ 12 | US$ 10 | `500 × {0,018 / 0,023 / 0,020}` |
| Banco gerenciado (2vCPU/8GB + 100GB) | US$ 117 | US$ 152 | US$ 118 | compute + 100 GB de disco |
| 10M req serverless | US$ 18 | US$ 19 | US$ 22 | Functions Consumption · Lambda · Cloud Functions |
| **Total mensal** | **≈ US$ 284** | **≈ US$ 322** | **≈ US$ 248** | — |
| **Total anual** | **≈ US$ 3.405** | **≈ US$ 3.864** | **≈ US$ 2.972** | `mensal × 12` |

> Detalhe do banco: **Azure** ≈ US$ 105 compute + US$ 11,50 storage; **AWS** ≈ US$ 140 compute (db.m5.large a US$ 0,192/h, ~2× a EC2 equivalente) + US$ 11,50 storage; **GCP** ≈ US$ 101 compute (`2×0,0413 + 8×0,007 = 0,1386/h`) + US$ 17 storage SSD.

#### Análise

**a) Mais barato?** **GCP** (≈ US$ 248/mês) — ~13% abaixo do Azure (US$ 284) e ~23% abaixo da AWS (US$ 322). A diferença vem do **compute** (a `e2-standard-2` a US$ 0,067/h é ~30% mais barata) e do **banco** (a AWS cobra prêmio claro pelo RDS). A diferença anualizada é real (~US$ 890/ano entre GCP e AWS), mas não é ordem de grandeza — para um time pequeno, os fatores não-financeiros do item (c) pesam mais.

**b) Reserved Instances de 1 ano na AWS (mais cara)?** Muda o ranking. Com _commitment_ de 1 ano (~35–39% off): 2 × m5.large → ~US$ 86/mês; RDS reservada → ~US$ 89/mês (+ storage); **novo total AWS ≈ US$ 217/mês**, abaixo do GCP _on-demand_. A leitura justa: as três oferecem 1 ano de compromisso com desconto parecido — se reservar uma, reserve as três, e o ranking volta a **GCP < Azure < AWS**, todas ~1/3 mais baratas. **Lição:** workload estável 24/7 nunca deveria ficar em _on-demand_.

**c) Outros fatores para um projeto de IA?** Em ordem: (1) serviços de IA gerenciados e modelos (Azure OpenAI / Bedrock / Vertex); (2) disponibilidade e cota de **GPU** + preço de _spot_; (3) **vector DB** nativo; (4) **data gravity e egress**; (5) região e **compliance (LGPD)**; (6) maturidade de IaC e _skills_ do time; (7) identidade e segurança gerenciadas (liga ao RBAC do Ex. 1.4).

---

### Exercício 2.3 — Estratégia de migração

*Responsável: Luciana Chaves D'Olivo.*

**a) Workload:** Sistema interno de **gestão de pedidos/atendimento** de uma empresa de médio porte: aplicação web monolítica em servidor on-premises, banco relacional na mesma máquina, usado em horário comercial por ~200 usuários, com picos previsíveis em campanhas. Infra envelhecendo, sem elasticidade e com janela de manutenção manual.

**b) Qual dos 6 Rs — _Replatform_ (lift, tinker & shift):**

| Dimensão | Análise |
|----------|---------|
| **Custo** | Médio. Mais que um Rehost puro, bem menos que um Refactor. Troca o servidor próprio por PaaS gerenciado (App Service + banco gerenciado) e elimina custo de manutenção de hardware/SO. |
| **Risco** | Baixo–médio. Não reescreve a aplicação; só ajusta config (conexão, variáveis, _storage_) e move o banco para serviço gerenciado. |
| **Ganho** | Alto. Elasticidade (escala nos picos), HA (alta disponibilidade) e _backup_ gerenciados, _patching_ automático e _deploy_ sem janela manual. |
| **Prazo** | Curto–médio (semanas). Mais rápido que Refactor; o esforço extra vs. Rehost compensa por já entregar PaaS. |

Não escolhemos **Rehost** puro (VM IaaS) porque manteria o fardo de gerenciar SO e _patching_; nem **Refactor** (microserviços) porque o ganho não justifica o custo/risco agora — fica como evolução futura.

**c) Serviço Azure + estimativa mensal** — preços de tabela _pay-as-you-go_, região **East US**, base **730 h/mês** (fonte: Azure Retail Prices API / calculadora oficial, jun/2026):

| Serviço | SKU / dimensionamento | Cálculo | Mensal |
|---------|-----------------------|---------|--------|
| **Azure App Service** (Linux) | Premium v3 **P1V3** (2 vCPU / 8 GB) | US$ 0,155/h × 730 | **US$ 113** |
| **Azure Database for PostgreSQL** (Flexible Server) | GP **D2ds_v5** (2 vCore) + 100 GB | (US$ 0,178/h × 730) + (100 × US$ 0,115) | **US$ 141** |
| **Azure Blob Storage** (anexos/uploads) | Hot LRS, 100 GB | 100 × US$ 0,018 | **US$ 2** |
| **Application Insights** (Azure Monitor) | ~10 GB ingestão/mês (5 GB grátis) | ~5 GB × US$ 2,30 | **US$ 12** |
| **Total** | | | **≈ US$ 268/mês** |


**d) Maior obstáculo e como endereçar:**
- **Técnico — migração do banco sem _downtime_ longo:** usar o **Azure Database Migration Service** com replicação contínua, validar em staging, fazer o _cutover_ numa janela curta de fim de semana e manter o on-premises como _fallback_ por alguns dias.
- **Organizacional — resistência da equipe** (sistema crítico, cultura on-premises): migração **incremental** (começar por homologação), treinamento e ganhos rápidos visíveis (deploy sem janela manual, dashboards). O obstáculo organizacional costuma ser maior que o técnico.

---

## 🔴 Nível 3 — Bônus

### Exercício 3.1 — Terraform: endurecer a segurança de rede da VM

*Responsável: Lucas Marujo Amadeu. Código em `terraform/` (`main.tf`, `variables.tf`, `outputs.tf`, `terraform.tfvars.example`); como rodar em `README.md`.*

Partindo do `main.tf` do lab (Atividade 5), foram feitas as quatro mudanças pedidas:

1. **SSH não fica mais aberto para o mundo.** A regra `SSH` do NSG saiu de `source_address_prefix = "*"` para `"${var.meu_ip}/32"`. O IP vem de uma **variável** `meu_ip` (sem _default_, com `validation` de formato IPv4), preenchida via `terraform.tfvars` a partir de `curl -s ifconfig.me`. Sem hardcode e sem segredo no código.
2. **Segunda subnet `subnet-app` (`10.0.2.0/24`)** na mesma VNet, como fundação para isolar a futura camada de aplicação da QC.
3. **Output do IP público** (`public_ip_address`) confirmado, além de `ssh_allowed_from` e `subnets` como outputs de verificação.
4. **Diff do `terraform plan`** traz **somente**:

| Símbolo | Recurso | Mudança |
|---------|---------|---------|
| `~` _update in-place_ | `azurerm_network_security_group.nsg` | regra `SSH`: `source_address_prefix` `"*"` → `"<meu_ip>/32"` |
| `+` _create_ | `azurerm_subnet.app` | nova subnet `subnet-app` (`10.0.2.0/24`) |

**A VM não é recriada** — `azurerm_linux_virtual_machine.vm` nem aparece no diff. Alterar uma regra de NSG e adicionar uma subnet são operações de rede que não tocam o ciclo de vida da VM.

**Boas práticas (Critério 3):** sem segredos no código (IP via _tfvars_, chave SSH via `file()`), variável com `validation`, comentários marcando cada mudança, e `terraform.tfvars.example` versionado em vez do `.tfvars` real.

### Exercício 3.2 — Bicep equivalente

*Responsável: Lucas Marujo Amadeu. Código em `bicep/main.bicep`; deploy e comparação em `README.md`.*

Como o repositório não traz o `template.json` ARM pronto, o `main.bicep` foi escrito diretamente a partir do Terraform endurecido (o enunciado permite os dois caminhos) e o `template.json` foi gerado com `bicep build` apenas para a contagem de linhas. O Bicep provisiona os mesmos recursos: VNet + 2 subnets + NSG (SSH travado no IP, HTTPS, HTTP) + IP público Standard + NIC + VM Ubuntu 24.04.

#### Comparação dos artefatos

| Artefato | Linhas | Observação |
|----------|--------|------------|
| `template.json` (ARM) | **248** | Gerado com `bicep build` no Cloud Shell |
| `main.tf` (Terraform, só o arquivo) | **173** | Versão endurecida do 3.1 |
| `terraform/` (módulo completo) | **258** | Base mais justa contra um Bicep que junta params+recursos+outputs |
| `main.bicep` | **207** | Arquivo único |

> Na comparação de **arquivo único**: `main.tf` **173** < `main.bicep` **207** < `template.json` ARM **248**. O ARM é a saída compilada do `bicep build` — sem comentários e cheio de `[resourceId(...)]`; ao mesmo tempo o **mais longo e o menos legível**.

**Qual ficou mais legível?** Ranking: **Bicep ≈ Terraform ≫ ARM JSON**. Entre Bicep e Terraform, para esta VM o **Terraform** ficou um pouco mais enxuto (o recurso `azurerm_linux_virtual_machine` "achata" as _nested properties_ que no Bicep ainda aparecem aninhadas). Mas o Bicep é muito melhor que o JSON cru e tem uma vantagem real: não exige _provider_ nem gerenciar _state file_.

**Quando escolher Bicep sobre Terraform?** Ambiente 100% Azure; ferramenta nativa Microsoft (suporte _day-0_ de recursos novos, integração com `az`, Azure Policy e `what-if`); não gerenciar _state_ (o Bicep usa o histórico de _deployment_ do ARM); time já no ecossistema Azure. **Quando ficar no Terraform:** multi-cloud, módulos reutilizáveis, `plan` explícito como _gate_, ecossistema maior. Para a trajetória da QC, **Terraform** segue como escolha principal; o Bicep entra como alternativa nativa em blocos exclusivamente Azure.

### Exercício 3.3 — Multi-cloud para a Quantum Commerce

*Responsável: Tatiana Mastrogiovanni.*

**a) Arquitetura multi-cloud (2+ provedores):**

| Workload | Nuvem | Justificativa |
|----------|-------|---------------|
| Agente de IA conversacional + RAG | **Azure** | Azure OpenAI (GPT-4o) + Azure AI Search com vector search nativo, melhor integração, SLA corporativo e conformidade LGPD/GDPR. |
| Data Lake e Analytics/BI | **AWS** | Amazon S3 + Redshift, ecossistema de analytics maduro e times de dados já treinados em AWS. |

**b) 4 desafios principais:**
1. **Latência entre nuvens** — chamadas cross-cloud (Azure↔AWS) adicionam 20–80 ms conforme as regiões. Mitigação: manter no mesmo provedor os serviços de alta frequência de comunicação, reservando o multi-cloud para workloads de acoplamento fraco.
2. **Identidade unificada** — Entra ID e AWS IAM são independentes. Solução: IdP central com federação para a AWS via IAM Identity Center usando OIDC/SAML.
3. **Custos de egress** — transferência entre provedores tem custo direto. Azure cobra ~US$ 0,087/GB de saída; 10 TB/mês ≈ US$ 890/mês só de egress. A arquitetura deve minimizar dados cruzando a fronteira entre nuvens.
4. **Observabilidade unificada** — logs e traces espalhados entre Azure Monitor e CloudWatch. Solução: ferramenta agnóstica (Datadog, Grafana Cloud ou OpenTelemetry) com backend centralizado e ingestão de ambos os provedores em um único dashboard.

**c) Terraform × Pulumi:**

| Critério | Terraform (HashiCorp) | Pulumi |
|----------|------------------------|--------|
| Linguagem | HCL (DSL própria) | Python, TypeScript, Go, C# |
| Pricing | Open Source + Terraform Cloud | Open Source + Pulumi Cloud (freemium) |
| Suporte Azure/AWS/GCP | Providers maduros nos 3 | Providers maduros nos 3 |
| Curva de aprendizado | Menor — HCL é simples e direto | Maior — requer proficiência na linguagem escolhida |
| Quando escolher | Padrão de mercado; times sem experiência em linguagens de programação | Times de engenharia com experiência em dev; lógica complexa (loops/condicionais), testes unitários de IaC; preferência por não aprender HCL |

Para a QC, **Terraform** é a escolha mais segura para o time atual (maior base de módulos prontos, mais fácil de contratar, onboarding mais rápido). Pulumi seria considerado apenas se o time de plataforma tivesse forte conhecimento em Python/TypeScript e precisasse de lógica de provisionamento muito dinâmica.

**d) Estimativa de egress (10 TB/mês, Azure Brazil South → AWS us-east-1):**
- Volume = 10 TB ≈ 10.240 GB (primeiros 10 GB gratuitos no Azure → ~10.230 GB cobrados)
- Azure egress: 10.230 GB × US$ 0,087 = **US$ 889,91/mês** · AWS ingress: gratuito
- **Total ≈ US$ 890/mês → US$ 10.680/ano**

**Azure Arc × AWS Outposts na QC:**
- **Azure Arc** permite gerenciar recursos AWS (VMs, clusters K8s) como se fossem recursos Azure, via Azure Policy, Defender for Cloud e Monitor de forma unificada — dando ao time de segurança da QC um dashboard único de compliance mesmo com workloads em dois provedores.
- **AWS Outposts** é hardware AWS instalado em datacenter próprio, para workloads com requisitos de ultra-baixa latência ou soberania de dados on-premise. Complementaria o modelo híbrido da QC em países com restrições regulatórias mais rígidas, onde dados financeiros não podem deixar o território nacional.

---

## Reflexão coletiva

Nesta primeira aula, o aprendizado mais importante do grupo foi perceber que **arquitetura, custo e segurança são decididos juntos, desde o dia 1** — não em etapas separadas. Saímos dos fundamentos (modelos de serviço, os 6 Rs, SLA, RBAC) e chegamos ao IaC entendendo que cada decisão conversa com as outras: a escolha de provedor na arquitetura define **quais** serviços entram; o comparativo de custos mostra que, para IA, a conta não é dominada pela VM, e sim por GPU, serviços cognitivos e egress; e o IaC é o que torna tudo **reprodutível e seguro**. Travar o SSH no IP via uma variável (em vez de `*` hardcoded) e versionar o `.example` em vez do `.tfvars` são o mesmo princípio que vamos precisar para os agentes da QC: **provisionamento determinístico e segredos fora do código**.

Conectando com uma plataforma **agentic**, ficou claro que um agente conversacional só funciona com as seis camadas conversando: serverless para escalar, **base vetorial para RAG**, LLM gerenciado para gerar a resposta, e observabilidade + RBAC para operar com segurança e auditabilidade. "Agente" não é só o modelo — é a plataforma cloud inteira por trás dele. A análise multi-cloud reforçou que decisões de provedor, lock-in e custo de egress são estratégicas e precisam ser pensadas cedo, antes que a _data gravity_ torne a mudança cara.

Se recomeçássemos o projeto QC hoje, já nasceríamos com **state remoto** no Terraform, **Reserved/Committed Use** no compute estável (em vez de _on-demand_) e segredos fora do código (Managed Identity + Key Vault) desde o primeiro provisionamento, em vez de adicionar essas práticas depois. Em resumo, a aula consolidou que boas decisões de **FinOps e de segurança** não são um passo final de "produção", e sim fundações que se desenham junto com a arquitetura.

---

## Artefatos do ZIP

- Documento principal: `entrega-grupo-aula01.md` (este arquivo)
- Diagrama: `diagramas/arquitetura-qc-aula01.png`
- Código IaC (Exercício 3.1): `terraform/` (`main.tf`, `variables.tf`, `outputs.tf`, `terraform.tfvars.example`)
- Código IaC (Exercício 3.2): `bicep/main.bicep`
- Instruções de execução do N3: `README.md`
