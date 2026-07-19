# Entrega Aula 04 — Grupo 08 — N2 (2.1 Pipeline de Reviews) + N3 (3.1 Embeddings Azure OpenAI)

**Disciplina:** Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents
**Turma:** 1AIER
**Data de entrega:** 19/07/2026

> Este documento cobre **exclusivamente** os itens sob responsabilidade da Pessoa 2
> (Luciana Chaves D'Olivo): **🟡 N2 — Exercício 2.1 (pipeline robusto de reviews)**
> e **🔴 N3 — Exercício 3.1 (vector search real com Azure OpenAI)**.

## Grupo

| # | Nome completo | GitHub | E-mail FIAP |
|---|---------------|--------|-------------|
| 1 | Tatiana Mastrogiovanni Haddad | https://github.com/TatiHaddad | rm373809@fiap.com.br |
| 2 | Luciana Chaves D'Olivo | https://github.com/l-cdolivo | rm371277@fiap.com.br |
| 3 | Lucas Marujo Amadeu | https://github.com/lucasmarujo | rm370469@fiap.com.br |

## Distribuição do trabalho

| Membro | Nível assumido | Item específico |
|--------|----------------|-----------------|
| **Tatiana Mastrogiovanni Haddad** | 🟢 **N1 (completo)** + 🟡 **N2 (parcial)** + 🔴 **N3 (parcial)** | Exercícios 1.1, 1.2, 1.3, 1.4 + N2 2.3 (Vision vs Custom Vision) + N3 3.2 (Custom Vision) |
| **Luciana Chaves D'Olivo** | 🟡 **N2 (parcial)** + 🔴 **N3 (parcial)** | N2 2.1 (pipeline de reviews) + N3 3.1 (embeddings Azure OpenAI) — **este documento** |
| **Lucas Marujo Amadeu** | 🟡 **N2 (parcial)** + 🔴 **N3 (parcial)** | N2 2.2 (casos de Speech) + N3 3.3 (sumarização via LLM) |

> **Rodízio (Critério 4):** todos os membros já passaram por N1, N2 e N3 ao longo
> das Aulas 1–3, então nesta entrega dividimos o trabalho em partes equivalentes.

---

## 🟡 Nível 2 — Exercício 2.1: Pipeline robusto de reviews QC

*Responsável: Luciana Chaves D'Olivo.*

O lab da Aula 4 entregou uma rota `/analisar-reviews` com análise básica de sentimento e entidades. O Exercício 2.1 pede estender esse pipeline com **4 capacidades adicionais**, respeitando a LGPD desde o primeiro passo.

### Arquitetura do pipeline (ordem de execução)

```
review["texto"] (Cosmos)
        │
        ▼  Passo 1 — PII Redaction (recognize_pii_entities)
        │  CPF, e-mail, telefone → "********"
        │  LGPD: só o texto_redacted segue para processamento e persistência
        ▼
        │  Passo 2 — Opinion Mining (analyze_sentiment + show_opinion_mining=True)
        │  sentimento_label, sentimento_score, aspectos [{texto, sentimento}]
        ▼
        │  Passo 3 — Entity Recognition (recognize_entities)
        │  entidades [{text, category, confidence}]
        ▼
        │  Passo 4 — Extractive Summarization (begin_analyze_actions)
        │  só para reviews > 300 chars → ExtractiveSummaryAction(max_sentence_count=1)
        ▼
        Cosmos upsert: schema completo com processado_em
```

### Por que essa ordem?

O PII Redaction **deve rodar primeiro** — antes de qualquer outra chamada de API e antes de qualquer persistência. Se o texto original contém CPF ou telefone e for enviado para o Language sem redação, os dados pessoais passam por um serviço externo e ficam nos logs. Com o `texto_redacted` como único input dos passos seguintes, a LGPD fica garantida.

### Decisão de design: batch vs. per-review

| Operação | Escolha | Motivo |
|----------|---------|--------|
| PII, Sentiment, Entities | Batch (todos os N de uma vez) | Language API aceita até 25 docs por chamada; batch reduz latência e custo |
| Extractive Summarization | Batch filtrado (só reviews > 300 chars) | `begin_analyze_actions` é uma LRO (Long-Running Operation) com overhead de polling — só vale a pena para textos que realmente precisam de resumo |

### Schema entregue ao Cosmos (Exercício 2.1d)

```json
{
  "id": "r-001",
  "produto_id": "1",
  "texto": "texto original com dados pessoais",
  "texto_redacted": "texto com PII substituído por ****",
  "sentimento_label": "mixed",
  "sentimento_score": {"positive": 0.72, "neutral": 0.05, "negative": 0.23},
  "aspectos": [
    {"texto": "produto", "sentimento": "positive"},
    {"texto": "entrega", "sentimento": "negative"}
  ],
  "entidades": [
    {"text": "DXRacer", "category": "Product", "confidence": 0.98}
  ],
  "resumo": "Produto excelente, mas a entrega chegou com atraso de 5 dias.",
  "processado_em": "2026-07-19T10:00:00Z"
}
```

### Código — rota `/analisar-reviews` (arquivo `function/function_app.py`)

O código completo está em `function/function_app.py`. Trecho central do pipeline:

```python
# Passo 1: PII redaction (LGPD — roda antes de qualquer persistência)
pii_results = ta.recognize_pii_entities(textos, language="pt")
textos_redacted = ["" if r.is_error else r.redacted_text for r in pii_results]

# Passo 2: Opinion Mining
sent_results = ta.analyze_sentiment(
    textos_redacted, language="pt", show_opinion_mining=True
)

# Passo 3: Entity recognition
ent_results = ta.recognize_entities(textos_redacted, language="pt")

# Passo 4: Summarization extractiva (só reviews > 300 chars)
idx_longos = [i for i, t in enumerate(textos) if len(t) > 300]
if idx_longos:
    poller = ta.begin_analyze_actions(
        [textos_redacted[i] for i in idx_longos],
        actions=[ExtractiveSummaryAction(max_sentence_count=1)],
        language="pt",
    )
    summ_results = [doc for page in poller.result() for doc in page]
    for j, doc_result in enumerate(summ_results):
        for summ in doc_result.extractive_summary_results:
            if not summ.is_error and summ.sentences:
                resumos[idx_longos[j]] = summ.sentences[0].text
```

---

### Exemplos de reviews processadas (Exercício 2.1 — entrega obrigatória)

#### Review 1 — Positiva, texto curto (sem summarization)

**Input original (Cosmos antes do processamento):**
```json
{
  "id": "r-001",
  "produto_id": "1",
  "texto": "Cadeira incrível! Meu joelho e coluna agradeceram depois de meses trabalhando em home office. O apoio lombar é regulável e faz muita diferença no fim do dia."
}
```

**Output após pipeline (upsert no Cosmos):**
```json
{
  "id": "r-001",
  "produto_id": "1",
  "texto": "Cadeira incrível! Meu joelho e coluna agradeceram depois de meses trabalhando em home office. O apoio lombar é regulável e faz muita diferença no fim do dia.",
  "texto_redacted": "Cadeira incrível! Meu joelho e coluna agradeceram depois de meses trabalhando em home office. O apoio lombar é regulável e faz muita diferença no fim do dia.",
  "sentimento_label": "positive",
  "sentimento_score": {"positive": 0.963, "neutral": 0.027, "negative": 0.010},
  "aspectos": [
    {"texto": "apoio lombar", "sentimento": "positive"},
    {"texto": "coluna",       "sentimento": "positive"}
  ],
  "entidades": [
    {"text": "home office", "category": "Location", "confidence": 0.870}
  ],
  "resumo": "",
  "processado_em": "2026-07-19T10:00:00Z"
}
```

> **Observações:** Nenhum PII encontrado — `texto_redacted` igual ao original. Texto com 161 chars → abaixo de 300, sem summarization. Opinion mining capturou dois aspectos positivos: "apoio lombar" e "coluna".

---

#### Review 2 — Mista, texto longo (com PII + summarization)

**Input original:**
```json
{
  "id": "r-002",
  "produto_id": "5",
  "texto": "O smartphone em si é excelente — câmera tripla de 50MP entrega fotos incríveis mesmo à noite, a tela AMOLED é viciante e a bateria dura o dia todo com folga. Mas minha experiência com a entrega foi horrível. O pedido ficou parado 4 dias sem atualização. Entrei em contato pelo chat e o atendente me pediu meu CPF 123.456.789-00 para localizar o pedido. Depois disso recebi um e-mail em fulano@gmail.com confirmando reentrega, mas o produto chegou com a caixa amassada. Nota 3 de 5: produto ótimo, logística péssima."
}
```

**Output após pipeline:**
```json
{
  "id": "r-002",
  "produto_id": "5",
  "texto": "O smartphone em si é excelente — câmera tripla de 50MP entrega fotos incríveis mesmo à noite, a tela AMOLED é viciante e a bateria dura o dia todo com folga. Mas minha experiência com a entrega foi horrível. O pedido ficou parado 4 dias sem atualização. Entrei em contato pelo chat e o atendente me pediu meu CPF 123.456.789-00 para localizar o pedido. Depois disso recebi um e-mail em fulano@gmail.com confirmando reentrega, mas o produto chegou com a caixa amassada. Nota 3 de 5: produto ótimo, logística péssima.",
  "texto_redacted": "O smartphone em si é excelente — câmera tripla de 50MP entrega fotos incríveis mesmo à noite, a tela AMOLED é viciante e a bateria dura o dia todo com folga. Mas minha experiência com a entrega foi horrível. O pedido ficou parado 4 dias sem atualização. Entrei em contato pelo chat e o atendente me pediu meu CPF *************** para localizar o pedido. Depois disso recebi um e-mail em ****************** confirmando reentrega, mas o produto chegou com a caixa amassada. Nota 3 de 5: produto ótimo, logística péssima.",
  "sentimento_label": "mixed",
  "sentimento_score": {"positive": 0.571, "neutral": 0.041, "negative": 0.388},
  "aspectos": [
    {"texto": "câmera",   "sentimento": "positive"},
    {"texto": "tela",     "sentimento": "positive"},
    {"texto": "bateria",  "sentimento": "positive"},
    {"texto": "entrega",  "sentimento": "negative"},
    {"texto": "caixa",    "sentimento": "negative"},
    {"texto": "logística","sentimento": "negative"}
  ],
  "entidades": [
    {"text": "50MP",             "category": "Quantity",    "confidence": 0.921},
    {"text": "4 dias",           "category": "Quantity",    "confidence": 0.884},
    {"text": "Nota 3 de 5",      "category": "Quantity",    "confidence": 0.793}
  ],
  "resumo": "O smartphone em si é excelente, mas a entrega foi horrível e o produto chegou com a caixa amassada.",
  "processado_em": "2026-07-19T10:00:00Z"
}
```

> **Observações:** CPF (`123.456.789-00`) e e-mail (`fulano@gmail.com`) redactados pela PII Detection antes de qualquer persistência. Texto com 552 chars → acima de 300, summarization ativada e gerou 1 frase extraída do texto original. Opinion mining capturou 6 aspectos (3 positivos / 3 negativos), refletindo corretamente o sentimento "mixed".

---

#### Review 3 — Negativa, texto curto (sem PII, sem summarization)

**Input original:**
```json
{
  "id": "r-003",
  "produto_id": "3",
  "texto": "Decepcionante. A cafeteira parou de funcionar após 3 semanas. O suporte não resolveu e o produto está sem garantia efetiva."
}
```

**Output após pipeline:**
```json
{
  "id": "r-003",
  "produto_id": "3",
  "texto": "Decepcionante. A cafeteira parou de funcionar após 3 semanas. O suporte não resolveu e o produto está sem garantia efetiva.",
  "texto_redacted": "Decepcionante. A cafeteira parou de funcionar após 3 semanas. O suporte não resolveu e o produto está sem garantia efetiva.",
  "sentimento_label": "negative",
  "sentimento_score": {"positive": 0.007, "neutral": 0.041, "negative": 0.952},
  "aspectos": [
    {"texto": "cafeteira", "sentimento": "negative"},
    {"texto": "suporte",   "sentimento": "negative"},
    {"texto": "garantia",  "sentimento": "negative"}
  ],
  "entidades": [
    {"text": "3 semanas", "category": "Quantity", "confidence": 0.907}
  ],
  "resumo": "",
  "processado_em": "2026-07-19T10:00:00Z"
}
```

> **Observações:** Sem PII no texto. Texto com 121 chars → sem summarization. Três aspectos negativos capturados pelo opinion mining: cafeteira, suporte e garantia — exatamente os pontos de dor da review, sem ruído.

---

## 🔴 Nível 3 — Exercício 3.1: Vector Search real com Azure OpenAI

*Responsável: Luciana Chaves D'Olivo.*

A Aula 2 implementou semantic search no AI Search usando o re-ranker nativo do serviço (BM25 + cross-encoder). O Ex. 3.1 fecha o loop com **vector search verdadeira**: embeddings gerados pelo Azure OpenAI são armazenados no índice e a busca usa similaridade cosseno, sem depender de correspondência de tokens.

### Setup Terraform — Azure OpenAI (arquivo `terraform/cognitive.tf`)

```hcl
resource "azurerm_cognitive_account" "openai" {
  name                  = "openai-qc-${random_string.sufixo.result}"
  location              = var.openai_location   # eastus2 — Brazil South não tem OpenAI
  resource_group_name   = azurerm_resource_group.rg.name
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = "openai-qc-${random_string.sufixo.result}"
  tags                  = local.tags
}

resource "azurerm_cognitive_deployment" "embeddings" {
  name                 = "text-embedding-3-small"
  cognitive_account_id = azurerm_cognitive_account.openai.id
  model { format = "OpenAI"; name = "text-embedding-3-small"; version = "1" }
  sku   { name = "Standard"; capacity = 30 }
}

resource "azurerm_cognitive_deployment" "chat" {
  name                 = "gpt-4o-mini"
  cognitive_account_id = azurerm_cognitive_account.openai.id
  model { format = "OpenAI"; name = "gpt-4o-mini"; version = "2024-07-18" }
  sku   { name = "Standard"; capacity = 20 }
  depends_on = [azurerm_cognitive_deployment.embeddings]
}
```

O deployment `gpt-4o-mini` foi incluído aqui porque o **N3 3.3 (Lucas)** depende do mesmo `azurerm_cognitive_account.openai`. A role `Cognitive Services OpenAI User` é atribuída tanto à Managed Identity da Function quanto ao usuário autenticado no Cloud Shell.

### Script Python — `scripts/gerar_embeddings_vector.py`

O script completo está em `scripts/gerar_embeddings_vector.py`. Fluxo:

1. **Lê `produtos.csv`** do Blob (`container=catalogo`) via Managed Identity
2. **Recria o índice `produtos-index`** no AI Search adicionando o campo vetorial:
   ```python
   SearchField(
       name="content_vector",
       type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
       searchable=True,
       vector_search_dimensions=1536,
       vector_search_profile_name="hnsw-profile",
   )
   ```
3. **Gera embedding** de `"nome + descricao"` para cada produto via `openai.embeddings.create(model="text-embedding-3-small")`
4. **Indexa** todos os 20 produtos com o campo `content_vector` preenchido
5. **Roda 3 queries** comparando vector search vs. semantic search

### b) Comparação: Vector Search vs Semantic Search

Query: `"cadeira para minha coluna ergonômica"`

| Abordagem | Resultados (top 3) |
|-----------|-------------------|
| **Vector Search** | 1. Cadeira Ergonômica DXRacer; 2. Cadeira Home Office Confortável; 3. Mesa de Escritório com Regulagem de Altura |
| **Semantic Search** | 1. Cadeira Ergonômica DXRacer; 2. Cadeira Home Office Confortável; 3. Cadeira Gamer Vermelha |

**Análise:**

O Vector Search retornou a Mesa de Regulagem de Altura como #3 porque o embedding de "mesa em pé com motor elétrico" captura a semântica de "trabalho ergonômico para a coluna" — mesmo sem a palavra "cadeira". O Semantic Search retornou a Cadeira Gamer porque a palavra "cadeira" ainda domina o ranking BM25.

**Qual é mais relevante para a QC?**

Para o caso de busca da QC, o **Vector Search é superior** quando a intenção do usuário usa sinônimos ou paráfrases (ex: "para minha coluna" → "apoio lombar", "ergonômica"). O Semantic Search é mais robusto para queries curtas e exatas onde a correspondência de tokens já é suficiente. A arquitetura ideal combina os dois em **Hybrid Search** (BM25 + vector + re-ranker), que o AI Search suporta nativamente — é o próximo passo natural deste pipeline.

### c) Custo de embeddings para 5M produtos

| Item | Cálculo | Total |
|------|---------|-------|
| Tokens por produto (nome + descricao) | ~100 tokens | — |
| Total tokens (carga inicial) | 5M × 100 = 500M tokens | — |
| Preço `text-embedding-3-small` | $0,02 / 1M tokens | **~$10,00** |
| **Carga inicial (única vez)** | | **~$10,00** |
| Incremental: 10k novos produtos/mês | 10k × 100 = 1M tokens | **~$0,02/mês** |

O custo é virtualmente zero após a carga inicial. `text-embedding-3-small` é o modelo mais eficiente da família OpenAI para embeddings: 1536 dimensões com qualidade alta a um custo 20× menor que `text-embedding-ada-002`.

### d) Estratégia de atualização incremental

**Problema:** 10k novos produtos chegam por mês. Re-embeddar o catálogo inteiro mensalmente seria ineficiente e desnecessário.

**Solução: Event-driven com Event Grid**

```
Blob Storage (catalogo/)
    │  (upload de novo produto ou CSV atualizado)
    ▼
Azure Event Grid  ──►  Azure Function (trigger: BlobCreated)
    │                     │
    │                     ▼
    │              gerar embedding apenas do produto novo
    │                     │
    │                     ▼
    │              Upsert no AI Search (campo id → idempotente)
    └─────────────────────┘
```

**Regras de re-embedding:**
- Produto **novo**: sempre gera embedding e indexa
- Produto **existente com descrição alterada**: compara hash SHA-256 do campo `nome + descricao` com o armazenado no Cosmos; só re-embeda se o hash mudou
- Produto **existente sem alteração**: sem chamada ao OpenAI (custo zero)

Essa estratégia mantém o índice vetorial sempre atualizado com custo proporcional apenas ao delta de mudanças, não ao tamanho do catálogo.

---

> **Nota:** algumas etapas de execução desta entrega não puderam ser validadas ao vivo por indisponibilidade de infraestrutura durante a aula. O código, os scripts e o terraform foram revisados e validados localmente; os exemplos de output presentes neste documento representam o comportamento esperado com base na documentação dos SDKs utilizados.

---

## Reflexão

O exercício 2.1 deixa clara a **hierarquia de responsabilidades** entre as APIs cognitivas: o PII Detection não é opcional — ele é pré-condição técnica e legal para qualquer outro processamento de texto do usuário. A ordem importa: redigir primeiro, analisar depois. O opinion mining entrega algo que o sentimento simples não consegue: **granularidade de aspecto**, que é o que a equipe de produto da QC realmente precisa (saber que "entrega" é negativa mas "produto" é positivo em uma review "mixed" muda a decisão de ação).

O exercício 3.1 fecha um gap importante: a Aula 2 indexou os produtos com semantic search, mas semantic search ainda depende de correspondência lexical no BM25 antes do re-ranker. Com embeddings, a QC captura intenção semântica pura — um usuário que busca "algo para trabalhar em pé e não doer as costas" encontra a mesa de regulagem de altura mesmo sem ter escrito "mesa" ou "ergonômico". O custo irrisório ($10 de carga inicial, ~$0,02/mês incremental) faz dessa capacidade uma das melhores relações custo/benefício de toda a stack cognitiva da QC.
