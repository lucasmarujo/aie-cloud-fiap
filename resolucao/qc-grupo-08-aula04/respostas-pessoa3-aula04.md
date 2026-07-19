# Entrega Aula 04 — Grupo 08 — N2 (2.2 Casos de Speech) + N3 (3.3 Sumarização de reviews via LLM)

**Disciplina:** Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents
**Turma:** 1AIER
**Data de entrega:** 19/07/2026

> Este documento cobre **exclusivamente** os itens sob responsabilidade da Pessoa 3
> (Lucas Marujo Amadeu): **🟡 N2 — Exercício 2.2 (casos de uso de Speech)** e
> **🔴 N3 — Exercício 3.3 (pipeline com LLM para sumarização de reviews)**.

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
| **Lucas Marujo Amadeu** | 🟡 **N2 (parcial)** + 🔴 **N3 (parcial)** | N2 2.2 (casos de Speech) + N3 3.3 (sumarização via LLM) — **este documento** |

> **Rodízio (Critério 4):** todos os membros já passaram por N1, N2 e N3 ao longo
> das Aulas 1–3, então nesta entrega dividimos o trabalho em partes equivalentes.
> O Lucas, que na Aula 3 assumiu o N2 completo, permanece em N2 + N3 aqui, agora
> na camada cognitiva (Speech) e no fechamento com LLM.

---

## 🟡 Nível 2 — Exercício 2.2: Casos de uso de Speech na Quantum Commerce

*Responsável: Lucas Marujo Amadeu.*

A QC hoje tem a camada de **Language** (sentimento, PII, entidades — Exercício 2.1)
e a de **Vision** (Exercício 2.3). O **Speech** fecha o canal de **voz**, que é onde
mais existe atrito não medido: o atendimento telefônico. Abaixo estão **3 casos de
uso concretos**, priorizados por relação custo/impacto — do mais alto ROI para o mais
estratégico.

> **Premissas de custo (Azure Speech, tier S0, Brazil South / PT-BR):**
> STT (Speech to Text) ≈ **$1,00/hora de áudio**; TTS (Text to Speech) Neural ≈
> **$16/1M de caracteres**. Valores usados na estimativa; a calculadora oficial
> deve ser conferida no fechamento do orçamento porque o preço de Neural TTS varia
> entre vozes padrão e HD.

---

### Caso 1 — Transcrição batch do atendimento por voz para análise pós-call

**a) Problema de negócio.**
A QC já analisa sentimento das **reviews escritas**, mas o call center gera ~50.000
horas/mês de conversas de voz que hoje **não entram no pipeline analítico**. Motivos
recorrentes de insatisfação (atraso de entrega, defeito, cobrança indevida) ficam
"presos" no áudio e só aparecem quando viram churn. O objetivo é transformar cada
ligação em texto e reaproveitar o **mesmo pipeline de Language** já construído no
Exercício 2.1 (PII redaction → sentimento → opinion mining), gerando visão agregada
por motivo de contato.

**b) STT ou TTS? Real-time ou batch?**
**STT em modo batch.** A análise é pós-call (não precisa de resposta durante a
ligação), então o **Batch Transcription API** é a escolha certa: processa lotes de
gravações do Blob de forma assíncrona, com custo menor e sem exigir streaming.

**c) Arquitetura proposta.**

```
Gravações (.wav) → Blob Storage (container "gravacoes")
        │  (trigger: Event Grid ao chegar novo blob)
        ▼
Azure Function  ──►  Speech Batch Transcription (STT PT-BR, diarização on)
        │                     │
        │                     ▼  transcrição bruta (JSON com timestamps + speaker)
        ▼
Pipeline de Language (reutiliza Ex. 2.1):
   recognize_pii_entities  → redige CPF/telefone ANTES de persistir (LGPD)
   analyze_sentiment (opinion mining) → aspecto+sentimento
        ▼
Cosmos DB (container "atendimentos") + agregação por motivo/produto
        ▼
Dashboard (Power BI / App Insights) — top motivos de insatisfação por semana
```

Componentes já existentes reaproveitados: **Blob Storage**, **Azure Function**,
**Managed Identity + Key Vault** (padrão de segurança do Exercício 1.3), **Cosmos DB**
e o **pipeline de Language** do Exercício 2.1. O único componente novo é o **Speech**.

**d) Volume mensal + custo.**

| Item | Volume | Preço unit. | Total mensal |
|------|--------|-------------|--------------|
| Speech Batch STT (PT-BR) | 50.000 h | ~$1,00/h | **~$50.000** |
| Language (sentiment + PII sobre o transcrito) | ~400M chars* | ~$2/1M chars | **~$800** |
| **Total** | | | **~$50.800/mês** |

\* 50.000 h × ~150 palavras/min × 60 min ≈ volume de texto na mesma ordem do
processamento de reviews; estimativa conservadora.

O STT domina o custo — é o item a otimizar (ver riscos). O reaproveitamento do
Language já existente torna o incremento analítico quase gratuito frente ao STT.

**e) Riscos.**
- **Qualidade em PT-BR:** áudio de call center tem ruído, sotaques e sobreposição de
  fala. Mitigação: ativar **diarização** (separar cliente/atendente) e, se o WER
  ficar alto em jargão da QC, treinar um **Custom Speech** com léxico próprio.
- **LGPD:** a gravação contém PII falada (CPF, cartão). A redação de PII precisa rodar
  **antes** de qualquer persistência do texto, e o áudio bruto deve ter retenção
  curta e acesso restrito por RBAC. Consentimento de gravação é pré-requisito legal.
- **Latência:** irrelevante aqui (batch), mas o SLA de processamento deve caber na
  janela de reporte semanal.

**f) Métricas de sucesso.**
- **WER (Word Error Rate)** < 15% em amostra auditada manualmente.
- **Cobertura:** % de ligações transcritas e classificadas (meta > 95%).
- **Impacto de negócio:** redução do tempo de detecção de um problema sistêmico
  (ex.: lote defeituoso) de semanas para dias; queda no **churn** dos contatos
  classificados como "mixed/negative".

---

### Caso 2 — URA cognitiva (self-service) para o FAQ de status de pedido e troca

**a) Problema de negócio.**
Grande parte das ligações é repetitiva e de baixo valor: "onde está meu pedido?",
"como faço uma troca?". Cada uma dessas consome um atendente humano. Uma **URA por
voz** que entende linguagem natural e responde falando resolve o caso simples e
libera o time humano para os casos complexos, reduzindo custo por contato e tempo de
espera.

**b) STT ou TTS? Real-time ou batch?**
**STT + TTS, ambos real-time (streaming).** O cliente fala → STT em tempo real → a
intenção é resolvida (RAG/tools da QC) → a resposta volta em voz via **Neural TTS**.
É um ciclo conversacional, então latência importa.

**c) Arquitetura proposta.**

```
Cliente (telefonia / app) 
   ▲ voz                    │ voz
   │ TTS Neural (PT-BR)     ▼ STT streaming (PT-BR)
        Orquestrador (Azure Function / Bot):
           - CLU para intenção ("rastrear_pedido", "trocar_produto")
           - chama as tools da QC (rota /produtos, /calcular_frete da Aula 3;
             status de pedido; política de troca via RAG no AI Search da Aula 2)
           - fallback: transbordo para humano se confiança baixa
```

Reaproveita as **tools de agente já expostas pela Function** (Aula 3) e o **RAG do
AI Search** (Aula 2) para a política de troca — a URA é só o novo canal de **voz**
sobre a mesma inteligência.

**d) Volume mensal + custo.**
Suponha 200.000 chamadas/mês, média 2 min de fala do cliente e ~1.500 caracteres de
resposta falada:

| Item | Volume | Preço unit. | Total mensal |
|------|--------|-------------|--------------|
| STT streaming | 200k × 2 min ≈ 6.667 h | ~$1,00/h | **~$6.667** |
| Neural TTS | 200k × 1.500 chars = 300M chars | ~$16/1M chars | **~$4.800** |
| **Total (Speech)** | | | **~$11.467/mês** |

Comparado ao custo de um atendente humano por ligação, o payback é rápido mesmo
desviando só uma fração das chamadas simples.

**e) Riscos.**
- **Qualidade PT-BR / frustração:** URA ruim gera raiva e mais transbordo. Mitigar
  com **threshold de confiança** e transbordo imediato para humano quando a intenção
  não é clara. TTS deve usar voz **Neural** (a voz robótica antiga derruba NPS).
- **Latência:** o ciclo STT→intenção→TTS precisa ficar abaixo de ~1–2 s para soar
  natural. Usar streaming e respostas curtas.
- **LGPD:** autenticar o cliente antes de expor dados de pedido; nunca falar dados
  sensíveis em voz sem verificação.

**f) Métricas de sucesso.**
- **Taxa de contenção (self-service):** % de chamadas resolvidas sem humano (meta
  30–40% no início).
- **NPS da URA** e **taxa de transbordo por frustração**.
- **Redução de custo por contato** e do tempo médio de espera na fila humana.

---

### Caso 3 — Acessibilidade: leitor automático das descrições de produto (TTS)

**a) Problema de negócio.**
O catálogo da QC é lido por milhões de usuários, incluindo pessoas com deficiência
visual e cenários de "mãos ocupadas" (dirigindo, cozinhando). Descrições apenas
textuais excluem esse público e reduzem conversão nesses contextos. Gerar **áudio da
descrição** amplia acessibilidade (inclusive obrigações legais de acessibilidade
digital) e cria um diferencial de experiência.

**b) STT ou TTS? Real-time ou batch?**
**TTS em modo batch** (pré-geração). As descrições mudam pouco; gerar o áudio uma vez
por produto e servir do CDN é muito mais barato e rápido do que sintetizar a cada
acesso. Regenera-se só quando a descrição muda.

**c) Arquitetura proposta.**

```
Catálogo (produtos.csv / Cosmos) 
        │ (job batch ou trigger on-change)
        ▼
Azure Function → Neural TTS (voz PT-BR) → arquivo .mp3
        ▼
Blob Storage (container "audio-catalogo") → CDN
        ▼
App/site tocam o áudio no player do produto (cache no cliente)
```

Reaproveita o **catálogo** já existente e o **Blob + Function**. Hash do texto da
descrição decide se precisa regenerar — evita re-sintetizar o que não mudou.

**d) Volume mensal + custo.**
Catálogo com 5M SKUs, descrição média de 300 caracteres, **geração única** + ~10k
produtos novos/mês:

| Item | Volume | Preço unit. | Custo |
|------|--------|-------------|-------|
| TTS carga inicial | 5M × 300 = 1,5B chars | ~$16/1M chars | **~$24.000 (única vez)** |
| TTS incremental | 10k × 300 = 3M chars/mês | ~$16/1M chars | **~$48/mês** |

O custo recorrente é irrisório graças ao cache — o peso está na carga inicial única.

**e) Riscos.**
- **Qualidade / naturalidade PT-BR:** nomes de marca e unidades ("120×60 cm") podem
  soar errados. Mitigar com **SSML** (pronúncia e pausas) nos campos críticos.
- **Latência:** não é problema (batch + CDN).
- **Custo de regeneração descontrolada:** se a descrição mudar com frequência, o TTS
  reprocessa. Mitigar com **hash de conteúdo** para só regenerar o que mudou.

**f) Métricas de sucesso.**
- **Conformidade de acessibilidade** (WCAG) e adoção do recurso (plays/produto).
- **Conversão** e tempo de permanência nas páginas com áudio vs sem.
- **% do catálogo com áudio disponível** (cobertura).

---

### Síntese do 2.2

| Caso | Serviço | Modo | Custo mensal aprox. | Prioridade |
|------|---------|------|---------------------|------------|
| 1. Pós-call analytics | STT | Batch | ~$50.800 | Alta (dado hoje invisível) |
| 2. URA cognitiva | STT + TTS | Real-time | ~$11.467 | Alta (reduz custo humano) |
| 3. Leitor de catálogo | TTS | Batch | ~$24k único + ~$48/mês | Média (acessibilidade) |

O padrão comum: **Speech é só o canal**; o valor vem de plugá-lo na inteligência que a
QC já tem (Language do Ex. 2.1, tools da Aula 3, RAG da Aula 2). Batch onde não há
interação; real-time só onde o cliente está no loop.

---

## 🔴 Nível 3 — Exercício 3.3: Pipeline com LLM — sumarização de reviews por produto

*Responsável: Lucas Marujo Amadeu.*

O Exercício 2.1 enriqueceu cada review individual (sentimento, aspectos, resumo de 1
frase). Mas quem toma decisão na QC não quer ler 800 reviews de um produto — quer a
**visão consolidada**: o que está bom, o que está ruim e **o que fazer**. Essa síntese
com priorização e recomendação de ação é exatamente onde o **LLM ganha** da API pronta.
Aqui adicionamos a rota `/sumarizar-reviews-produto` ao `function_app.py`.

### a–d) Rota `/sumarizar-reviews-produto`

A rota recebe `produto_id`, lê **todas as reviews já enriquecidas** desse produto no
Cosmos (schema do Exercício 2.1), monta um prompt estruturado e chama o
**Azure OpenAI `gpt-4o-mini`** exigindo saída em JSON. Autenticação por **Managed
Identity** (padrão do Exercício 1.3 — sem API key no código), usando o mesmo custom
subdomain do Azure OpenAI provisionado no Exercício 3.1.

```python
# Trecho adicionado ao function_app.py — rota /sumarizar-reviews-produto (Ex. 3.3)
import os
import json
import logging

import azure.functions as func
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.cosmos import CosmosClient
from openai import AzureOpenAI

# --- Configuração (injetada pelo Terraform via App Settings) ---
OPENAI_ENDPOINT   = os.environ["AZURE_OPENAI_ENDPOINT"]          # https://openai-qc-xxxx.openai.azure.com/
OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
COSMOS_ENDPOINT   = os.environ["COSMOS_ENDPOINT"]
COSMOS_DB         = os.environ.get("COSMOS_DB", "quantumcommerce")
COSMOS_CONTAINER  = os.environ.get("COSMOS_CONTAINER_REVIEWS", "reviews")

_credential = DefaultAzureCredential()

# Token AAD via Managed Identity — nenhuma API key no código (Ex. 1.3)
_token_provider = get_bearer_token_provider(
    _credential, "https://cognitiveservices.azure.com/.default"
)
_openai = AzureOpenAI(
    azure_endpoint=OPENAI_ENDPOINT,
    azure_ad_token_provider=_token_provider,
    api_version="2024-10-21",
)
_cosmos = CosmosClient(COSMOS_ENDPOINT, credential=_credential)
_reviews_container = _cosmos.get_database_client(COSMOS_DB).get_container_client(COSMOS_CONTAINER)

SYSTEM_PROMPT = (
    "Você é um analista de e-commerce da Quantum Commerce. Analise as reviews do "
    "produto e responda SOMENTE com um JSON válido no formato:\n"
    '{\n'
    '  "resumo_geral": "1-2 frases",\n'
    '  "pontos_positivos": ["..."],\n'
    '  "pontos_negativos": ["..."],\n'
    '  "recomendacoes_de_acao": ["..."]\n'
    "}\n"
    "Baseie-se apenas nas reviews fornecidas. Não invente fatos. Priorize os "
    "aspectos mais recorrentes."
)


def _ler_reviews(produto_id: str) -> list[dict]:
    """Lê todas as reviews enriquecidas (Ex. 2.1) de um produto no Cosmos."""
    query = "SELECT r.texto_redacted, r.sentimento_label, r.aspectos FROM r WHERE r.produto_id = @pid"
    params = [{"name": "@pid", "value": produto_id}]
    return list(
        _reviews_container.query_items(
            query=query, parameters=params, enable_cross_partition_query=True
        )
    )


def _montar_reviews_texto(reviews: list[dict]) -> str:
    linhas = []
    for r in reviews:
        aspectos = ", ".join(
            f'{a["texto"]}:{a["sentimento"]}' for a in r.get("aspectos", [])
        )
        linhas.append(
            f'- ({r.get("sentimento_label", "n/a")}) {r.get("texto_redacted", "")}'
            + (f" [aspectos: {aspectos}]" if aspectos else "")
        )
    return "\n".join(linhas)


@app.route(route="sumarizar-reviews-produto", methods=["GET"])
def sumarizar_reviews_produto(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/sumarizar-reviews-produto?produto_id=5 (Ex. 3.3)."""
    produto_id = (req.params.get("produto_id") or "").strip()
    if not produto_id:
        return _json_response({"erro": "produto_id é obrigatório"}, 400)

    try:
        reviews = _ler_reviews(produto_id)
    except Exception as e:
        logging.exception("Falha ao ler reviews do Cosmos")
        return _json_response({"erro": f"falha ao acessar cosmos: {e!s}"}, 500)

    if not reviews:
        return _json_response({"erro": "produto sem reviews"}, 404)

    user_prompt = (
        f"Produto: {produto_id}\n\nReviews:\n{_montar_reviews_texto(reviews)}"
    )
    try:
        completion = _openai.chat.completions.create(
            model=OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        analise = json.loads(completion.choices[0].message.content)
    except Exception as e:
        logging.exception("Falha na chamada ao Azure OpenAI")
        return _json_response({"erro": f"falha no llm: {e!s}"}, 502)

    return _json_response(
        {
            "produto_id": produto_id,
            "total_reviews": len(reviews),
            "analise": analise,
        }
    )
```

> **Notas de engenharia (por que assim):**
> - `response_format={"type": "json_object"}` garante JSON parseável — evita o clássico
>   "o modelo devolveu texto solto e o parse quebrou".
> - `temperature=0.2`: síntese factual, não texto criativo. Queremos consistência.
> - **Managed Identity + custom subdomain** (Ex. 1.3): role `Cognitive Services OpenAI User`
>   para a MI da Function, zero chave no código.
> - Reusa `_json_response` e o `app = func.FunctionApp(...)` já existentes no
>   `function_app.py` da Aula 3 — a rota é um incremento, não uma aplicação nova.

**Exemplo de saída** (`GET /api/sumarizar-reviews-produto?produto_id=5`):

```json
{
  "produto_id": "5",
  "total_reviews": 128,
  "analise": {
    "resumo_geral": "Produto bem avaliado pela qualidade e custo-benefício, mas com reclamações consistentes sobre prazo de entrega.",
    "pontos_positivos": [
      "Qualidade do material acima do esperado",
      "Bom custo-benefício",
      "Montagem simples"
    ],
    "pontos_negativos": [
      "Entrega atrasou em vários pedidos",
      "Embalagem chegou danificada em alguns casos"
    ],
    "recomendacoes_de_acao": [
      "Revisar SLA da transportadora na região com mais atrasos",
      "Reforçar embalagem de proteção",
      "Destacar a qualidade do material na descrição do anúncio"
    ]
  }
}
```

### e) LLM vs Language API pronta — quando cada uma ganha

| Dimensão | Language API (L₃ / Ex. 2.1) | LLM (`gpt-4o-mini`) |
|----------|------------------------------|----------------------|
| Sentimento por review | ✅ Ótimo, barato, determinístico | Redundante e mais caro |
| Extração de aspectos (opinion mining) | ✅ Estruturado, rótulo por aspecto | Faz, mas menos previsível |
| PII redaction | ✅ Especializado, deve rodar antes | ❌ Não é o papel dele |
| **Síntese consolidada de N reviews** | ❌ Não sumariza cross-review com juízo | ✅ **É aqui que ganha** |
| **Recomendações de ação priorizadas** | ❌ Não infere ação de negócio | ✅ **É aqui que ganha** |
| Custo / previsibilidade | Muito baixo, saída fixa | Maior, saída generativa |

**Conclusão:** as duas são **complementares, não concorrentes**. A Language API pronta
faz o trabalho de **volume por review** (barato, estruturado, com PII redaction
obrigatória antes) e **alimenta** o LLM. O LLM entra **uma vez por produto** para o que
a API pronta não faz: **consolidar, priorizar e recomendar ação**. Usar LLM para
sentimento review-a-review seria caro e redundante; usar Language para gerar
"recomendações de ação" é impossível. O pipeline certo é **Language primeiro, LLM por
cima**.

### f) Custo para 5M produtos × 50 reviews/produto

Estimativa de tokens por chamada (1 chamada por produto, agregando suas ~50 reviews):

- **Input:** system (~150 tokens) + 50 reviews × ~60 tokens ≈ **~3.150 tokens/produto**
- **Output:** JSON consolidado ≈ **~300 tokens/produto**

Preços `gpt-4o-mini`: **$0,15/1M input** + **$0,60/1M output**.

| Componente | Cálculo | Total |
|-----------|---------|-------|
| Input | 5M × 3.150 = 15,75B tokens × $0,15/1M | **~$2.363** |
| Output | 5M × 300 = 1,5B tokens × $0,60/1M | **~$900** |
| **Total (carga única, todos os produtos)** | | **~$3.263** |

**Otimizações que derrubam o custo recorrente:**
- **Só recalcular quando muda:** re-sumarizar apenas produtos com **novas reviews**
  desde a última execução, não o catálogo inteiro. A maioria dos 5M SKUs não recebe
  review nova por mês.
- **Threshold de recálculo:** disparar re-sumarização a cada N reviews novas (ex.: +10)
  ou por janela de tempo, não a cada review — evita chamada por evento.
- **Prompt caching** do system prompt (constante) reduz o custo de input repetido.

Assim, os ~$3,3k são um custo **de carga inicial única**; o recorrente cai para a
fração de produtos ativos que efetivamente recebem reviews novas no período.

---

## Reflexão (contribuição da Pessoa 3)

A camada de Speech e a sumarização por LLM reforçam a tese central da entrega: a
arquitetura evolui de **API pronta → custom → LLM** conforme o produto amadurece, e a
decisão é sempre **custo × qualidade × abertura do problema**. Speech e Language
prontos resolvem o volume por baixo custo e devem vir primeiro (e, no caso de PII/voz,
por obrigação de LGPD, antes de qualquer persistência). O LLM entra **cirurgicamente**
no topo, só onde é preciso raciocínio aberto — consolidar reviews e recomendar ação —
e com controle de custo por recálculo incremental. É esse encaixe (pronto na base,
LLM na ponta) que torna o pipeline útil para o agente da QC decidir sem estourar o
orçamento.
