# Entrega Aula 04 — Grupo 08

**Disciplina:** Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents
**Turma:** 1AIER
**Data de entrega:** 19/07/2026

> Documento principal consolidado do ZIP. As respostas individuais completas estão
> em `respostas-pessoa1-aula04.md`, `respostas-pessoa2-aula04.md` e
> `respostas-pessoa3-aula04.md`. O código está em `function/`, `scripts/` e `terraform/`.

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
| **Luciana Chaves D'Olivo** | 🟡 **N2 (parcial)** + 🔴 **N3 (parcial)** | N2 2.1 (pipeline de reviews) + N3 3.1 (embeddings Azure OpenAI) |
| **Lucas Marujo Amadeu** | 🟡 **N2 (parcial)** + 🔴 **N3 (parcial)** | N2 2.2 (casos de Speech) + N3 3.3 (sumarização via LLM) |

> **Rodízio (Critério 4):** todos os membros já passaram por N1, N2 e N3 ao longo
> das Aulas 1–3, então nesta entrega dividimos o trabalho em partes equivalentes,
> cada um assumindo uma fatia de N2 + N3 na nova camada cognitiva.

---

## 🟢 Nível 1 — Fundamentos

*Responsável: Tatiana Mastrogiovanni Haddad.*

### Exercício 1.1 — Pronto vs Custom vs LLM

| Caso de uso | Pronta | Custom | LLM | Justificativa |
|-------------|--------|--------|-----|---------------|
| Detectar idioma de uma review | ✅ | | | Language Detection cobre 100+ idiomas, custo baixo, sem treino. |
| Classificar produtos em 5 categorias da QC (jargão próprio) | | ✅ | | Vocabulário interno que modelos genéricos não conhecem → CLU/Custom Vision com rótulos proprietários. |
| Gerar descrição de produto a partir da foto + specs | | | ✅ | Síntese multimodal criativa (imagem + texto) → GPT-4o com visão. |
| Transcrever áudio de atendimento em PT-BR | ✅ | | | Speech to Text pronto tem ótima performance em PT-BR. |
| Extrair CPF, e-mail, telefone de chat (LGPD) | ✅ | | | PII Detection é otimizado para entidades pessoais e suporta PT-BR; mais barato e seguro que LLM. |
| Responder pergunta aberta sobre política de troca | | | ✅ | Exige intenção + geração contextual → LLM + RAG (AI Search). |
| OCR de etiqueta nutricional | ✅ | | | Read API extrai texto impresso com alta precisão, barato. |
| Identificar peças industriais da empresa em foto | | ✅ | | Vocabulário visual proprietário → Custom Vision treinado internamente. |

### Exercício 1.2 — Custo mensal

| Serviço | Volume | Preço unit. (S0) | Total mensal |
|---------|--------|-----------------|--------------|
| Language (sentiment + entities) | 400M chars | ~$2/1M chars | **$800** |
| Speech batch (PT-BR) | 50.000h | ~$1/hora | **$50.000** |
| Vision Read + Tags | 500.000 chamadas | ~$1,50/1k | **$750** |
| **Total** | | | **$51.550/mês** |

**a) Serviço que pesa mais:** Speech ($50.000/mês, ~97% do total). Ação prática: avaliar transcrever amostra representativa em vez de 100% das chamadas.

**b) Sentiment via GPT-4o-mini (50 in + 10 out por review):**
`(50 × $0,15/1M) + (10 × $0,60/1M) = $0,0000135/review` → 2M reviews = **$27/mês**.
Comparado aos ~$800/mês da Language API, o **LLM sai ~30× mais barato** para textos curtos, porque a Language cobra por caractere e o GPT-4o-mini por token.

**c) Quando trocar API pronta por LLM mesmo mais caro:** vocabulário muito específico da QC (a API pronta erra as entidades do catálogo); decisão crítica (review que pode gerar recall/crise); ou quando o LLM entrega aspectos + resumo + ação + tom numa única chamada (a API pronta exigiria 3-4 chamadas).

### Exercício 1.3 — Segurança: autenticação da Function no AI Services

| Estratégia | Recomendado? | Razão |
|-----------|--------------|-------|
| API Key hardcoded em `function_app.py` | **NÃO** | Vaza no primeiro commit; qualquer fork/histórico expõe a chave. |
| API Key como Application Setting | **Não ideal** | Quem tem Contributor no portal vê o valor. Só para dev. |
| API Key no Key Vault via MI | **OK didático** | Tira a chave do código, mas overhead — AI Services já suporta MI direta. |
| Token AAD via Managed Identity direto no AI Services | ✅ **Padrão produção** | Sem chave em código, config ou Vault. |

**2 pré-requisitos para MI direta:**
1. **Custom subdomain** habilitado (`custom_subdomain_name` no `azurerm_cognitive_account`) — sem ele o SDK não faz auth AAD.
2. **Role assignment** `Cognitive Services User` na MI da Function no escopo do recurso — sem ela o token é válido mas retorna **403**.

### Exercício 1.4 — Vision capabilities map

| Cenário | Capacidade | Justificativa |
|---------|-----------|---------------|
| Auto-categorizar produto novo do vendedor | **Tags** | Rótulos semânticos genéricos mapeados para o catálogo; sem treino. |
| Encontrar produtos visualmente similares | **Image Embedding** | Vetor da imagem + similaridade de cosseno no AI Search (RAG visual). |
| Contar produtos numa prateleira | **Object Detection** | Precisa de bounding boxes para contar/localizar. |
| Extrair preço da etiqueta | **OCR (Read API)** | Texto impresso com números/moeda; simples e barato. |
| Gerar alt-text para acessibilidade | **Caption** | Frase descritiva da imagem. |
| Identificar pessoas na foto (LGPD) | **Object Detection** (ou Face API) | Detecta presença de pessoas; Face API é mais precisa para anonimizar rostos. |
| Classificar os 12 modelos "QC Premium" | **Custom Vision** | Modelos exclusivos não existem em modelo genérico. |

---

## 🟡 Nível 2 — Pipeline e Decisões

### Exercício 2.1 — Pipeline robusto de reviews QC

*Responsável: Luciana Chaves D'Olivo.* Código: `function/function_app.py` → rota `/analisar-reviews`.

**Ordem do pipeline (a ordem importa por LGPD):**

```
review["texto"] (Cosmos)
  ▼ Passo 1 — PII Redaction (recognize_pii_entities): CPF/e-mail/telefone → "****"
  ▼ Passo 2 — Opinion Mining (analyze_sentiment show_opinion_mining=True): label + aspectos
  ▼ Passo 3 — Entity Recognition (recognize_entities)
  ▼ Passo 4 — Extractive Summarization (begin_analyze_actions, só reviews > 300 chars)
  ▼ Cosmos upsert: schema completo + processado_em
```

O **PII Redaction roda primeiro**: só o `texto_redacted` alimenta os passos seguintes e é o único que pode ser persistido, garantindo LGPD desde o início.

**Schema persistido no Cosmos (2.1d):**

```json
{
  "id": "r-001", "produto_id": "1",
  "texto": "...", "texto_redacted": "...",
  "sentimento_label": "mixed",
  "sentimento_score": {"positive": 0.72, "neutral": 0.05, "negative": 0.23},
  "aspectos": [{"texto": "entrega", "sentimento": "negative"}],
  "entidades": [{"text": "DXRacer", "category": "Product", "confidence": 0.98}],
  "resumo": "...", "processado_em": "2026-07-19T10:00:00Z"
}
```

**3 exemplos de reviews processadas** (obrigatório) — versões completas em `respostas-pessoa2-aula04.md`:

- **Review 1 (positiva, curta):** sem PII, 161 chars → sem resumo. `sentimento_label: positive` (0.963). Aspectos: "apoio lombar" (+), "coluna" (+).
- **Review 2 (mista, longa, com PII):** CPF `123.456.789-00` e e-mail `fulano@gmail.com` **redactados antes de persistir**. 552 chars → summarization ativada. `sentimento_label: mixed` (pos 0.571 / neg 0.388). 6 aspectos (câmera/tela/bateria + / entrega/caixa/logística −).
- **Review 3 (negativa, curta):** sem PII, 121 chars → sem resumo. `sentimento_label: negative` (0.952). Aspectos: cafeteira, suporte, garantia (todos −).

### Exercício 2.2 — Casos de uso de Speech na QC

*Responsável: Lucas Marujo Amadeu.* Detalhamento completo (itens a–f) em `respostas-pessoa3-aula04.md`.

> **Premissas de custo (Speech S0, PT-BR):** STT ≈ $1,00/hora; Neural TTS ≈ $16/1M chars.

| Caso | Serviço | Modo | Custo mensal aprox. | Prioridade |
|------|---------|------|---------------------|------------|
| 1. Pós-call analytics (transcreve call center → pipeline de Language 2.1) | STT | Batch | ~$50.800 | Alta (dado hoje invisível) |
| 2. URA cognitiva (self-service FAQ de pedido/troca) | STT + TTS | Real-time | ~$11.467 | Alta (reduz custo humano) |
| 3. Leitor de catálogo (acessibilidade, áudio das descrições) | TTS | Batch | ~$24k único + ~$48/mês | Média (acessibilidade) |

**Padrão comum:** Speech é só o **canal**; o valor vem de plugá-lo na inteligência que a QC já tem (Language do 2.1, tools da Aula 3, RAG da Aula 2). **Batch** onde não há interação, **real-time** só onde o cliente está no loop. Riscos recorrentes: qualidade PT-BR (mitigar com diarização/Custom Speech), latência (streaming na URA) e LGPD (redigir PII falada antes de persistir; consentimento de gravação).

### Exercício 2.3 — Vision pronto vs Custom Vision

*Responsável: Tatiana Mastrogiovanni Haddad.* Análise completa em `respostas-pessoa1-aula04.md`.

**a) Custo (50k imagens/mês):**

| | Opção 1 (Vision pronto + LLM) | Opção 2 (Custom Vision) |
|---|---|---|
| Custo mensal | ~**$76/mês** ($75 Vision + $1,35 LLM) | ~**$100/mês** (50k × $2/1k predição) |
| Setup inicial | $0 | Rotulagem ~6.000 imagens (~200h humanas) |
| Manutenção trimestral | Ajustar prompt (minutos) | +20 categorias ≈ +800 imagens rotuladas |

**b) Qualidade:** Vision+LLM ~70-80% (cai a ~50% em categorias similares, pois usa tags genéricas); Custom Vision ~90% (treinado no catálogo, fundo branco padronizado).

**c) Manutenção (+20 categorias/trimestre):** Vision+LLM só ajusta o prompt (rápido), risco de confundir categorias similares com o tempo; Custom Vision exige coletar/rotular ~800 imagens e retreinar — gargalo é a rotulagem humana, que cresce sem parar.

**d) Recomendação (híbrida):** Camada 1 = **Custom Vision** para as top ~30 categorias (Pareto: ~70% do volume, ~$70/mês); Camada 2 = **Vision pronto + LLM** para as 120 restantes (~$23/mês). Uma Function roteia por categoria prevista. Total ~**$93/mês** — mais barato que Custom puro e com qualidade superior no alto volume. Ideal para MVP, migrando categorias de maior impacto para Custom ao longo do tempo.

---

## 🔴 Nível 3 — Embeddings Reais e LLMs (bônus)

### Exercício 3.1 — Vector Search real com Azure OpenAI

*Responsável: Luciana Chaves D'Olivo.* Código: `scripts/gerar_embeddings_vector.py`; IaC: `terraform/cognitive.tf`.

O script lê os 20 produtos do Blob, recria o índice `produtos-index` com o campo vetorial `content_vector` (1536 dim, perfil HNSW), gera embeddings de `nome + descricao` com `text-embedding-3-small` e roda 3 queries.

**b) Vector vs Semantic** — query `"cadeira para minha coluna ergonômica"`:

| Abordagem | Top 3 |
|-----------|-------|
| **Vector Search** | Cadeira Ergonômica DXRacer · Cadeira Home Office · **Mesa com Regulagem de Altura** |
| **Semantic Search** | Cadeira Ergonômica DXRacer · Cadeira Home Office · Cadeira Gamer Vermelha |

O Vector captura a **intenção** ("trabalho ergonômico para a coluna" → mesa em pé) mesmo sem a palavra "cadeira"; o Semantic ainda é dominado pelo token "cadeira" (BM25). Para a QC, o **Vector é superior** em sinônimos/paráfrases; o ideal é **Hybrid Search** (BM25 + vector + re-ranker), suportado nativamente pelo AI Search.

**c) Custo 5M produtos:** 5M × 100 tokens = 500M tokens × $0,02/1M = **~$10 (carga única)**; incremental de 10k/mês ≈ **$0,02/mês**.

**d) Atualização incremental:** event-driven com **Event Grid** (BlobCreated → Function → embedding só do produto novo → upsert idempotente por `id`). Produto existente re-embeda só se o hash SHA-256 de `nome + descricao` mudar — custo proporcional ao delta, não ao catálogo.

### Exercício 3.2 — Custom Vision para a linha "QC Premium"

*Responsável: Tatiana Mastrogiovanni Haddad.*

> ⚠️ **Não entregue nesta versão.** É item bônus; a execução no portal Custom Vision
> (criar projeto, treinar, publicar, print do dashboard, URL da prediction API e custo
> de 50k/mês) ficou pendente. A decisão de produto pronto vs Custom Vision está
> coberta no Exercício **2.3**.

### Exercício 3.3 — Pipeline com LLM: sumarização de reviews por produto

*Responsável: Lucas Marujo Amadeu.* Código: `function/function_app.py` → rota `/sumarizar-reviews-produto`. Teste: `function/test_sumarizar_reviews_produto.py`.

A rota recebe `produto_id`, lê **todas as reviews já enriquecidas** (schema do 2.1) no Cosmos, monta um prompt estruturado e chama o Azure OpenAI `gpt-4o-mini` exigindo saída JSON. Autenticação por **Managed Identity** (custom subdomain do OpenAI do 3.1, role `Cognitive Services OpenAI User`), sem API key no código.

**Notas de engenharia:** `response_format={"type":"json_object"}` garante JSON parseável; `temperature=0.2` para síntese factual; reusa `app`, `_credential` e `_json_response` do `function_app.py`; guard de `_openai` quando o endpoint não está configurado (→ 503).

**Exemplo de saída** (`GET /api/sumarizar-reviews-produto?produto_id=5`):

```json
{
  "produto_id": "5",
  "total_reviews": 128,
  "analise": {
    "resumo_geral": "Produto bem avaliado pela qualidade e custo-benefício, mas com reclamações consistentes sobre prazo de entrega.",
    "pontos_positivos": ["Qualidade do material acima do esperado", "Bom custo-benefício", "Montagem simples"],
    "pontos_negativos": ["Entrega atrasou em vários pedidos", "Embalagem chegou danificada em alguns casos"],
    "recomendacoes_de_acao": ["Revisar SLA da transportadora na região com mais atrasos", "Reforçar embalagem", "Destacar a qualidade na descrição"]
  }
}
```

**e) LLM vs Language API pronta:** são **complementares**. A Language pronta faz o trabalho de **volume por review** (sentimento, aspectos, PII redaction obrigatória antes) — barato e estruturado — e **alimenta** o LLM. O LLM entra **uma vez por produto** para o que a API pronta não faz: **consolidar N reviews, priorizar e recomendar ação**. Usar LLM review-a-review seria caro e redundante; usar Language para "recomendações de ação" é impossível.

**f) Custo 5M produtos × 50 reviews:** input ~3.150 tk/produto + output ~300 tk/produto → **~$3.263 de carga única** ($2.363 input + $900 output). Recorrente cai muito com recálculo incremental (só produtos com reviews novas), threshold de N reviews e prompt caching do system prompt.

---

## Reflexão coletiva

**1. O que aprendemos de mais importante nesta aula.**
A lição central foi que serviços cognitivos não são intercambiáveis: existe uma **tríade pronto → custom → LLM** e escolher errado custa caro em dinheiro ou em qualidade. O exercício de custo (1.2) foi revelador — descobrimos que o GPT-4o-mini é ~30× mais barato que a Language API para sentimento de textos curtos (token vs caractere), enquanto o Speech domina 97% do orçamento e é onde a otimização importa. Também internalizamos que **segurança não é opcional**: Managed Identity com custom subdomain + role é o padrão de produção, e API key hardcoded vaza no primeiro commit. E que **LGPD é pré-condição técnica**, não etapa final — o PII Redaction tem que rodar antes de qualquer persistência ou chamada externa, o que definiu a própria ordem do pipeline 2.1.

**2. Como isso se conecta com a arquitetura cloud de uma plataforma agentic.**
As três camadas que construímos são exatamente as **ferramentas do agente** da QC. O Language pronto (2.1) enriquece cada review a baixo custo; o Speech (2.2) abre o canal de voz plugado na mesma inteligência; os embeddings reais (3.1) fecham o RAG começado na Aula 2, dando ao agente busca por intenção e não só por token; e o LLM (3.3) entra no topo para raciocínio aberto — consolidar e recomendar ação. O encaixe é **pronto na base, LLM na ponta**: o agente decide sobre dados já estruturados e baratos, e só gasta LLM onde há valor. Managed Identity é o que faz tudo isso conversar sem espalhar credenciais — o mesmo padrão de identidade que sustenta um sistema multi-agente seguro.

**3. Que decisão arquitetural faríamos diferente hoje.**
Começaríamos o índice do AI Search já com **Hybrid Search** (BM25 + vetor + re-ranker) desde a Aula 2, em vez de evoluir de semantic para vector depois — o custo de embeddings é irrisório (~$10 de carga única) e teríamos evitado retrabalho de re-indexação. No lado de IaC, definiríamos as **App Settings do OpenAI na Function junto do resto do stack** desde o início (aprendemos isso corrigindo o gap do Terraform desta entrega), em vez de injetá-las depois. E adotaríamos **recálculo incremental por hash de conteúdo** como padrão desde o dia 1 em toda operação cara (embeddings e sumarização por LLM), tratando "só reprocessar o que mudou" como princípio de arquitetura, não como otimização posterior.

---

## Artefatos do ZIP

- **Documento principal:** este `entrega-grupo-aula04.md` (+ `respostas-pessoa1/2/3-aula04.md` com o detalhe completo)
- **Diagrama:** `diagramas/arquitetura-qc-aula04.md` (Mermaid — camada cognitiva Speech/Language/Vision + LLM)
- **Código IaC:** `terraform/` (`main.tf`, `cognitive.tf`, `variables.tf` — Azure OpenAI + embeddings + gpt-4o-mini + roles + app settings)
- **Function:** `function/function_app.py` (5 rotas) + `requirements.txt` + `test_sumarizar_reviews_produto.py`
- **Scripts:** `scripts/gerar_embeddings_vector.py` (3.1) + `scripts_dependencia_aula2/` (setup Aula 2)
- **Como rodar:** `README.md` (deploy + `curl` de cada rota)
