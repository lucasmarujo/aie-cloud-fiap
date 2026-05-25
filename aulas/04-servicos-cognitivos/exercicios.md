# Exercícios — Aula 4

**Tema:** Serviços Cognitivos & APIs
**Formato:** **Entrega obrigatória por grupo** — ZIP no Portal FIAP
**Vale:** 10% da nota final ([rubrica completa](../../entregas/rubrica.md))
**Prazo:** 1 dia antes da Aula 5
**Como entregar:** ver [entregas/entrega-04/INSTRUCOES.md](../../entregas/entrega-04/INSTRUCOES.md)

---

## Instruções gerais

Esta é a **4ª entrega de grupo** da disciplina. Os 3 níveis são **divisão de trabalho dentro do grupo**:

- 🟢 **Nível 1 — Básico:** ecossistema cognitivo, pricing, segurança (API key vs MI), Vision capabilities
- 🟡 **Nível 2 — Intermediário:** pipeline robusto de reviews QC, casos de uso de Speech, pronto vs custom
- 🔴 **Nível 3 — Avançado:** **bônus opcional** — embeddings reais com Azure OpenAI (fecha o loop do AI Search da Aula 2), Custom Vision, sumarização de reviews via LLM

**Mínimo obrigatório:** N1 + N2 cobertos. **N3 é bônus** (até +2 pts extras).

### Distribuição entre membros (sugerida)

- Iniciantes: N1 — consolidação dos 3 tipos de serviços cognitivos
- Intermediários: N2 — estender o pipeline com sumarização e segmentação
- Experientes: N3 — Azure OpenAI para embeddings e RAG completo

> **Rodízio:** quem fez N1 nas Aulas 1-3 deve assumir N2 ou N3 agora.

### Template obrigatório

Use o [template em `entregas/template-entrega-grupo.md`](../../entregas/template-entrega-grupo.md) para o `entrega-grupo-aula04.md` dentro do ZIP.

> **Política "no install":** Tudo no Azure Cloud Shell.

---

## 🟢 Nível 1 — Básico: Consolidando os Fundamentos

### Exercício 1.1 — Pronto vs Custom vs LLM

Para cada caso da Quantum Commerce, marque a opção mais adequada (**API pronta**, **modelo customizado** ou **LLM**) e justifique em 1-2 frases:

| Caso de uso | Pronta | Custom | LLM | Justificativa |
|-------------|--------|--------|-----|---------------|
| Detectar idioma de uma review | | | | |
| Classificar produtos em 5 categorias da QC (jargão próprio) | | | | |
| Gerar descrição de produto a partir da foto + specs | | | | |
| Transcrever áudio de atendimento em PT-BR | | | | |
| Extrair CPF, e-mail, telefone de chat (LGPD) | | | | |
| Responder pergunta aberta do cliente sobre política de troca | | | | |
| OCR de etiqueta nutricional | | | | |
| Identificar peças industriais da empresa em foto de estoque | | | | |

<details>
<summary>Sugestões de gabarito</summary>

- Detectar idioma: **Pronta** (Language Detection, $0/1k para textos pequenos)
- Categorias com jargão próprio QC: **Custom (CLU ou Custom Vision)** — vocabulário próprio
- Descrição de produto: **LLM** — abertura criativa
- Transcrever PT-BR: **Pronta** (Speech) — modelo bem treinado em PT
- Extrair PII: **Pronta** (PII Detection do Language) — otimizada para isso
- Pergunta aberta sobre política: **LLM** + RAG com docs da política
- OCR etiqueta: **Pronta** (Read API)
- Peças industriais: **Custom Vision** — vocabulário não cabe em modelo genérico

</details>

---

### Exercício 1.2 — Calcule o custo mensal

A Quantum Commerce processa por mês:

- **2M de reviews** para análise de sentimento (média 200 chars cada → 400M chars)
- **50.000 horas de atendimento** transcritas (Speech)
- **500k imagens de produto** analisadas (Vision)

Use a [calculadora Azure](https://azure.microsoft.com/pricing/calculator) e preencha:

| Serviço | Volume | Preço unit. (S0) | Total mensal |
|---------|--------|-----------------|--------------|
| Language (sentiment + entities) | 400M chars | ~$2/1M chars | |
| Speech batch (PT-BR) | 50.000h | ~$1/h | |
| Vision Read + Tags | 500.000 chamadas | ~$1.50/1k | |
| **Total** | | | |

**Análise:**

a) Qual serviço pesa mais no orçamento mensal?
b) Se substituir Sentiment pela Azure OpenAI (GPT-4o-mini @ ~$0.15/1M input + $0.60/1M output), quanto custaria? (Considere ~50 input tokens + 10 output tokens por review)
c) Em que cenário vale a pena trocar API pronta por LLM mesmo sendo mais caro?

---

### Exercício 1.3 — Segurança: como sua Function autentica no AI Services?

Marque a estratégia recomendada para produção e justifique:

| Estratégia | Recomendado? | Razão |
|-----------|--------------|-------|
| API Key hardcoded em `function_app.py` | | |
| API Key como Application Setting da Function | | |
| API Key no Key Vault, lida pela Function via MI no Vault | | |
| Token AAD via Managed Identity diretamente no AI Services | | |

**Pergunta extra:** Para o último caso (MI direta), quais são os 2 pré-requisitos no recurso AI Services para que funcione? (Dica: subdomínio + role)

<details>
<summary>Sugestão</summary>

- Hardcoded → **NÃO** (vaza no repo)
- App Setting → **Não ideal** (quem tem portal vê)
- Key Vault via MI → **OK didático mas overhead**
- **MI direto no AI Services** → ✅ **padrão para produção**

Pré-requisitos para MI direto:

1. **Custom subdomain** habilitado no `azurerm_cognitive_account` (`custom_subdomain_name`)
2. **Role assignment:** `Cognitive Services User` para a MI da Function

</details>

---

### Exercício 1.4 — Vision capabilities map

Para cada cenário da QC, marque qual capacidade do Vision usar (**Tags**, **OCR (Read)**, **Object Detection**, **Caption**, **Image Embedding**, **Custom Vision**):

| Cenário | Capacidade | Justificativa |
|---------|-----------|---------------|
| Auto-categorizar produto novo enviado pelo vendedor | | |
| Encontrar produtos visualmente similares ao da busca | | |
| Detectar quantos produtos estão na prateleira de uma loja física | | |
| Extrair preço da etiqueta de um produto fotografado | | |
| Gerar texto alternativo (alt-text) para acessibilidade | | |
| Identificar se a foto tem 1 ou mais pessoas (anonimização LGPD) | | |
| Classificar entre os 12 modelos próprios da linha "QC Premium" | | |

---

## 🟡 Nível 2 — Intermediário: Pipeline e Decisões

### Exercício 2.1 — Pipeline robusto de reviews QC

O lab L₃ implementou uma análise simples de sentimento + entidades. Estenda o pipeline com:

a) **Summarization extractive:** para reviews >300 chars, gerar resumo de 1 frase. Use `azure-ai-textanalytics` → `analyze_actions` com `ExtractiveSummarizationAction`.

b) **PII Detection:** rodar antes da análise, redigindo CPF/e-mail/telefone do texto. Implementar usando `recognize_pii_entities`.

c) **Opinion Mining:** identificar **aspectos** mencionados na review e o sentimento de cada (ex: "entrega" → negativo, "qualidade" → positivo). Usar `analyze_sentiment` com `show_opinion_mining=True`.

d) **Persistência estruturada:** atualizar o documento no Cosmos com schema:

```json
{
  "id": "r-001",
  "produto_id": "5",
  "texto": "Adorei o produto, mas a entrega demorou demais",
  "texto_redacted": "...",
  "sentimento_label": "mixed",
  "sentimento_score": {"positive": 0.6, "negative": 0.3, "neutral": 0.1},
  "aspectos": [
    {"texto": "produto", "sentimento": "positive"},
    {"texto": "entrega", "sentimento": "negative"}
  ],
  "entidades": [...],
  "resumo": "...",
  "processado_em": "2026-06-22T14:30:00Z"
}
```

**Entrega:** código atualizado + 3 exemplos de reviews processadas no `entrega-grupo-aula04.md`.

---

### Exercício 2.2 — Casos de uso de Speech na QC

Proponha **3 casos de uso** concretos de Speech (STT ou TTS) para a Quantum Commerce e detalhe cada um:

**Para cada caso, responda:**

a) Qual o problema de negócio?
b) STT ou TTS? Real-time ou batch?
c) Arquitetura proposta (que componentes da QC envolve?)
d) Estimativa de volume mensal + custo
e) Riscos (qualidade em PT-BR, latência, LGPD)
f) Métricas de sucesso (qualidade, NPS, conversão)

Exemplos de inspiração:

- URA (Unidade de Resposta Audível) para FAQ
- Transcrição automática de atendimento por voz para análise pós-call
- Acessibilidade: leitor automático das descrições de produto
- Busca por voz no app/site
- Geração de áudio para anúncios em rádio

---

### Exercício 2.3 — Quando treinar modelo próprio?

A Quantum Commerce está decidindo entre Vision pronto vs Custom Vision para classificar imagens de produtos.

**Dados:**

- 5M de SKUs, organizados em 150 categorias específicas da QC (ex: "sofá-3-lugares-modular", "tapete-shaggy-redondo")
- 90% das imagens são em fundo branco padronizado
- Para cada categoria existem ~30-50 imagens rotuladas internamente
- Volume de classificação: 50k imagens/mês

**Sua tarefa:**

a) Calcule o custo mensal das 2 abordagens:
   - **Vision pronto + LLM para mapear tags genéricas → categoria QC:** Vision $0.0015 × 50k + GPT-4o-mini $X
   - **Custom Vision treinado:** treino inicial + storage + predição

b) Compare em termos de **qualidade esperada** — qual cobre melhor o vocabulário específico?

c) Compare em **manutenção:** como cada um se comporta quando a QC adiciona 20 novas categorias por trimestre?

d) Faça uma **recomendação justificada** considerando custo + qualidade + manutenção. Se possível, proponha uma arquitetura **híbrida** (ex: Custom para os 20 top vendedores + Pronto para o resto).

---

## 🔴 Nível 3 — Avançado: Embeddings Reais e LLMs

### Exercício 3.1 — Fechar o loop: Vector Search verdadeira com Azure OpenAI

A Aula 2 implementou semantic search no AI Search. Agora vamos fazer **vector search real** com embeddings gerados por **Azure OpenAI** (`text-embedding-3-small`, 1536 dim).

#### Setup

1. Provisione um **Azure OpenAI** no Terraform da Aula 4 (region: `eastus2` ou `swedencentral` — Brazil South não tem ainda):

```hcl
resource "azurerm_cognitive_account" "openai" {
  name                  = "openai-qc-${random_string.sufixo.result}"
  location              = "eastus2"
  resource_group_name   = azurerm_resource_group.rg.name
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = "openai-qc-${random_string.sufixo.result}"
}

resource "azurerm_cognitive_deployment" "embeddings" {
  name                 = "text-embedding-3-small"
  cognitive_account_id = azurerm_cognitive_account.openai.id
  model {
    format  = "OpenAI"
    name    = "text-embedding-3-small"
    version = "1"
  }
  sku {
    name     = "Standard"
    capacity = 30
  }
}
```

2. Adicione role `Cognitive Services OpenAI User` para sua identidade do Cloud Shell.

#### Tarefa

a) Escreva um script Python que:
   1. Lê os 20 produtos do Blob (`produtos.csv` da Aula 2)
   2. Para cada produto, gera embedding de `nome + descricao` usando `text-embedding-3-small`
   3. Re-indexa no AI Search (criado na Aula 2) com novo campo `content_vector` de 1536 dim
   4. Roda 3 queries semânticas e mostra resultados

b) Compare com o **semantic search** original da Aula 2:
   - Query: "cadeira para minha coluna ergonômica"
   - Vector search retornou: ___
   - Semantic search retornou: ___
   - Qual é mais relevante para a QC? Por quê?

c) Calcule o **custo** de gerar embeddings para os 5M de produtos da QC:
   - Média 100 tokens por produto (nome + descricao curta)
   - 5M × 100 = 500M tokens
   - Preço: $0.02 / 1M tokens (text-embedding-3-small)
   - **Total:** ~$10 (única vez) + reprocessamento incremental

d) Discuta: como você manteria os embeddings **atualizados** quando produtos novos chegam (10k/mês)?

---

### Exercício 3.2 — Custom Vision para classificar a linha "QC Premium"

A QC tem uma linha exclusiva "Premium" com 12 modelos próprios. Vision pronto não os reconhece.

**Tarefa:**

a) Acesse [Custom Vision](https://www.customvision.ai/) com sua conta Azure.

b) Crie um projeto **Image Classification — Multiclass** com 3 tags fictícias da linha QC (ex: `qc-sofa-premium`, `qc-poltrona-premium`, `qc-mesa-premium`).

c) Para cada tag, faça upload de **15-20 imagens** (pode usar imagens livres do Unsplash para simulação).

d) **Treine** o modelo (Quick Training — ~5 min, gratuito).

e) Avalie: precision/recall do modelo no validation set.

f) **Publique** o modelo e teste via API REST.

g) Documente no `entrega-grupo-aula04.md`:
   - Print do dashboard com métricas
   - URL da prediction API
   - Custo estimado para 50k predições/mês

---

### Exercício 3.3 — Pipeline com LLM: resumir reviews por produto

Estenda o pipeline da Aula 4 com uma rota `/sumarizar-reviews-produto`:

a) Recebe `produto_id` como query param

b) Lê **todas as reviews** desse produto do Cosmos (já enriquecidas com sentimento)

c) Chama Azure OpenAI (`gpt-4o-mini`) com prompt estruturado:

```
Você é um analista de e-commerce. Analise as reviews abaixo do produto {nome_produto} e retorne em JSON:
{
  "resumo_geral": "1-2 frases",
  "pontos_positivos": [...],
  "pontos_negativos": [...],
  "recomendacoes_de_acao": [...]
}

Reviews:
{lista de reviews com sentimento}
```

d) Retorna o JSON estruturado

e) Compare com a versão **só com Language API** do L₃ — em que casos o LLM ganha? Em que casos a Language API pronta seria suficiente?

f) **Custo:** estime para 5M produtos com média de 50 reviews/produto.

---

## Critérios de entrega

A entrega é **um ZIP por grupo** (`entrega-grupo-NN-aula04.zip`) no Portal FIAP. Estrutura completa, prazo e dicas de geração do ZIP em [entregas/entrega-04/INSTRUCOES.md](../../entregas/entrega-04/INSTRUCOES.md).

| Item | Obrigatório? | Pontos máximos |
|------|--------------|----------------|
| Cabeçalho do grupo + distribuição do trabalho | ✅ Sim | 1 pt (Critério 4) |
| 🟢 N1 — Exercícios 1.1, 1.2, 1.3, 1.4 | ✅ Sim | 3 pts (Critério 1) |
| 🟡 N2 — 2.1 (pipeline robusto), 2.2 (Speech use cases), 2.3 (Vision pronto vs Custom) | ✅ Sim | 3 pts (Critério 2) + 2 pts qualidade técnica (Critério 3) |
| 🔴 N3 — 3.1 (embeddings reais), 3.2 (Custom Vision), 3.3 (LLM summarization) | 🎁 Bônus | até +2 pts extras |
| Reflexão coletiva ao final | ✅ Sim | 1 pt (Critério 5) |
| **Total da entrega** | | **10 pts** (10% da nota final) |

**Prazo:** 1 dia antes da Aula 5.
**Onde:** upload do ZIP no Portal FIAP. Apenas 1 membro do grupo faz o upload.
