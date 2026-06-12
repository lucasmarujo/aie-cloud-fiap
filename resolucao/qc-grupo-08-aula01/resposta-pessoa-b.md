# Entrega Aula 01 — Grupo 08 · Contribuição da Pessoa B

**Linha da Pessoa B para a tabela "Distribuição do trabalho":**

| Membro                 | Nível assumido      | Item específico                                                                |
|------------------------|---------------------|--------------------------------------------------------------------------------|
| Luciana Chaves D'Olivo | 🟡 N2 + coordenação | Exercício 2.1 (arquitetura + diagrama) + 2.3; montagem do doc, reflexão e ZIP  |

**Artefatos que a Pessoa B entrega no ZIP:**
- `diagramas/arquitetura-qc-aula01.png` (diagrama do Exercício 2.1 — **obrigatório**)
- `entrega-grupo-08-aula01.md` (documento consolidado do grupo)
- A reflexão coletiva (seção final do documento)

---

## 🟡 Nível 2 — Exercício 2.1 — Arquitetura de alto nível: Quantum Commerce

**Contexto:** QC = e-commerce em 12 países, 5M de SKUs, querendo experiência de compra com **IA conversacional**. A arquitetura precisa suportar agentes conversacionais com **base vetorial** (RAG sobre o catálogo) e **APIs serverless**, que é a contribuição desta disciplina para o case.

### 1. Camadas da arquitetura

Proponho **6 camadas**, do usuário até a operação:

| # | Camada | O que faz | Por que existe na QC |
|---|--------|-----------|----------------------|
| 1 | **Edge / Entrega** | CDN, WAF e DNS global; serve frontend e imagens de produto perto do usuário | 12 países → latência e cache de imagens de 5M SKUs são críticos |
| 2 | **Frontend / Experiência** | Web/app + a interface do **chat conversacional** | É o ponto de contato com o cliente  |
| 3 | **API / Orquestração** | APIs serverless (HTTP) + **orquestração do agente**: recebe a pergunta, decide ferramentas, chama IA e dados | Coração do projeto: serverless é escalável |
| 4 | **Dados** | Catálogo (Banco NoSQL para lidar com as diferentes características de produtos), pedidos/clientes (Banco SQL), imagens (blob storage) e a **base vetorial** (embeddings do catálogo para RAG) | O agente só responde bem se recupera o produto certo  |
| 5 | **IA / Cognitiva** | LLM conversacional, busca semântica, e serviços cognitivos (visão para busca por imagem, sentimento de reviews) | É o que transforma a QC de e-commerce em e-commerce **agentic** |
| 6 | **Observabilidade & Segurança** | Logs, métricas, tracing, gestão de identidade e segredos (Key Vault) | Agente em produção precisa ser auditável, seguro e rastreável (custo de token, alucinação, abuso) |

**Como as camadas conversam (fluxo de uma pergunta do cliente):**
`Cliente → (1) CDN/WAF → (2) Frontend/Chat → (3) API serverless + Orquestrador do agente → (5) LLM` ; o orquestrador, antes de responder, faz **(4) busca vetorial** no catálogo (RAG) e consulta os bancos relacional/NoSQL para preço e estoque; **(6)** observabilidade e identidade permeiam todas as camadas.

### 2. Provedor principal — **Azure** (e por quê)

Escolho **Azure** como nuvem principal da QC, por quatro motivos:

1. **IA conversacional madura e gerenciada** — **Azure OpenAI / AI Foundry** entrega os modelos de LLM com SLA corporativo, cota dedicada e isolamento de rede, que é exatamente o núcleo do case (agente conversacional). É o diferencial mais forte para a QC.
2. **Vector DB nativo** — **Azure AI Search** já tem busca vetorial + híbrida integrada, encurtando a camada de RAG sem montar um vetor DB separado.
3. **Identidade e segurança first-class** — Entra ID + Managed Identity + RBAC granular (o que a Pessoa A mapeou no Ex. 1.4) reduzem segredos no código e custam menos esforço operacional.
4. **Compliance e região** — disponibilidade de **Brazil South** ajuda na LGPD para os dados de clientes brasileiros, e o ecossistema Azure (Bicep, Azure Policy) está alinhado ao que a disciplina já usa nos labs.

### 3. Serviços por categoria

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

### 4. Diagrama (a desenhar no Excalidraw / draw.io — **sem instalar nada**)


---

## 🟡 Nível 2 — Exercício 2.3 — Estratégia de migração

**a) Workload (genérico):** Sistema interno de **gestão de pedidos/atendimento** de uma empresa de médio porte: aplicação web monolítica em servidor on-premises, banco relacional na mesma máquina, usado em horário comercial por ~200 usuários, com picos previsíveis em campanhas. Infra envelhecendo, sem elasticidade e com janela de manutenção manual.

**b) Qual dos 6 Rs — _Replatform_ (lift, tinker & shift):**

| Dimensão | Análise |
|----------|---------|
| **Custo** | Médio. Mais que um Rehost puro, bem menos que um Refactor. Troca o servidor próprio por PaaS gerenciado (App Service + banco gerenciado) e elimina custo de manutenção de hardware/SO. |
| **Risco** | Baixo–médio. Não reescreve a aplicação; só ajusta config (conexão, variáveis, _storage_) e move o banco para serviço gerenciado. Bem menos arriscado que microservicializar. |
| **Ganho** | Alto. Ganha elasticidade (escala nos picos), Alta disponibilidade e _backup_ gerenciados, _patching_ automático e _deploy_ sem janela manual. |
| **Prazo** | Curto–médio (semanas). Mais rápido que Refactor; o esforço extra vs. Rehost compensa por já entregar PaaS. |

Não escolhi **Rehost** puro (só uma VM IaaS) porque manteria o fardo de gerenciar SO e _patching_; nem **Refactor** (microserviços) porque o ganho não justifica o custo/risco agora — fica como evolução futura.

**c) Serviço Azure + estimativa mensal** — preços de tabela _pay-as-you-go_, região **East US**, base **730 h/mês** (fonte: Azure Retail Prices API / calculadora oficial, jun/2026):

| Serviço | SKU / dimensionamento | Cálculo | Mensal |
|---------|-----------------------|---------|--------|
| **Azure App Service** (Linux) | Premium v3 **P1V3** (2 vCPU / 8 GB) | US$ 0,155/h × 730 | **US$ 113** |
| **Azure Database for PostgreSQL** (Flexible Server) | GP **D2ds_v5** (2 vCore) + 100 GB | (US$ 0,178/h × 730) + (100 × US$ 0,115) | **US$ 141** |
| **Azure Blob Storage** (anexos/uploads) | Hot LRS, 100 GB | 100 × US$ 0,018 | **US$ 2** |
| **Application Insights** (Azure Monitor) | ~10 GB ingestão/mês (5 GB grátis) | ~5 GB × US$ 2,30 | **US$ 12** |
| **Total** | | | **≈ US$ 268/mês** |


**d) Maior obstáculo e como endereçar:**
- **Técnico — migração do banco sem perda/_downtime_ longo:** usar o **Azure Database Migration Service** com replicação contínua, validar em ambiente de staging, fazer o _cutover_ numa janela curta de fim de semana e manter o on-premises como _fallback_ por alguns dias.
- **Organizacional — resistência/medo da equipe** (sistema crítico, cultura on-premises): endereçar com migração **incremental** (começar por ambiente de homologação), treinamento, e mostrando ganho rápido (deploy sem janela manual, dashboards de monitoramento). O obstáculo organizacional costuma ser maior que o técnico.

---

## 💭 Reflexão coletiva — consolidação (tarefa de coordenação da Pessoa B)


1. **O que o grupo aprendeu de mais importante?** — Dos fundamentos (modelos de serviço, 6 Rs, SLA, RBAC) até IaC: a percepção de que **arquitetura, custo e segurança são decididos juntos, desde o dia 1**. A escolha de provedor (2.1) define quais serviços entram; o comparativo (2.2) mostra que, em IA, a conta é dominada por GPU/serviços cognitivos e egress, não pela VM; e o IaC (3.1/3.2) é o que torna tudo reprodutível.

2. **Conexão com arquitetura _agentic_** — Um agente conversacional só funciona com as 6 camadas conversando: serverless para escalar, **base vetorial para RAG**, LLM gerenciado para gerar, e observabilidade + RBAC para operar com segurança. A QC mostra que "agente" não é só o modelo — é a plataforma cloud inteira por trás.

3. **O que faríamos diferente hoje** — Já nascer com **state remoto** no Terraform, **Reserved/Committed Use** no compute estável, e segredos fora do código (Managed Identity + Key Vault) desde o primeiro provisionamento, em vez de adicionar depois.

---

## ✅ Checklist de coordenação da Pessoa B (antes do upload)

- [X] Montar `entrega-grupo-aula01.md` a partir do [template](../../../entregas/template-entrega-grupo.md), colando: cabeçalho do grupo + N1 (de A) + 2.1/2.3 (meu) + 2.2/3.1/3.2 (de C) + 3.3 (de A) + reflexão consolidada
- [X] Preencher a **data de entrega** no cabeçalho (07/06/2026)
- [X] Exportar o **diagrama** → `diagramas/arquitetura-qc-aula01.png`
- [X] Recolher **1 frase da Pessoa A** para a reflexão e fechar os 3–5 parágrafos
- [X] Conferir que o ZIP **não** contém `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`
- [X] Nome do ZIP: `entrega-grupo-08-aula01.zip`, pasta interna `qc-grupo-08-aula01/`
- [X] Confirmar com a Pessoa C que `terraform destroy` / `az group delete` foram rodados
- [ ] **1 só membro** faz o upload no Portal FIAP
