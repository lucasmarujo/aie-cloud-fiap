# Entrega Aula 04 — Grupo 08 — N1 (1.1, 1.2, 1.3, 1.4 ) + N2 (2.3 Vision vs Custom Vision) + N3 (3.2 Custom Vision)

**Disciplina:** Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents
**Turma:** 1AIER
**Data de entrega:** 19/07/2026


## Grupo

| # | Nome completo | GitHub | E-mail FIAP |
|---|---------------|--------|-------------|
| 1 | Tatiana Mastrogiovanni Haddad | https://github.com/TatiHaddad | rm373809@fiap.com.br |
| 2 | Luciana Chaves D'Olivo | https://github.com/l-cdolivo | rm371277@fiap.com.br |
| 3 | Lucas Marujo Amadeu | https://github.com/lucasmarujo | rm370469@fiap.com.br |

## Distribuição do trabalho

| Membro | Nível assumido | Item específico |
|--------|----------------|-----------------|
| **Tatiana Mastrogiovanni Haddad** | 🟢 **N1 (completo)** + 🟡 **N2 (parcial)** + 🔴 **N3 (parcial)** |  Exercícios 1.1, 1.2, 1.3, 1.4 + N2 2.3 (Vision vs Custom Vision) + N3 3.2 Custom Vision |
| **Luciana Chaves D'Olivo** | 🟡 **N2 (parcial)** + 🔴 **N3 (parcial)** | N2 2.1 (pipeline reviews) + N3 3.1 (embeddings Azure OpenAI) |
| **Lucas Marujo Amadeu** | 🟡 **N2 (parcial)** + 🔴 **N3 (parcial)**  | N2 2.2 (casos de Speech) + N3 3.3 (sumarização LLM) |



> **Rodízio (Critério 4):** Como todos já passaram por todos os níveis, resolvemos dividir em partes iguais


 
---
 
## 🟢 Nível 1 — Fundamentos
 
### Exercício 1.1 — Pronto vs Custom vs LLM

| Caso de uso | Pronta | Custom | LLM | Justificativa |
|-------------|--------|--------|-----|---------------|
| Detectar idioma de uma review | ✅ | | | Language Detection é bem treinado para 100+ idiomas, tem custo baixo (~$0/1k para textos pequenos), sem necessidade de treinamento customizado. |
| Classificar produtos em 5 categorias da QC (jargão próprio) | | ✅ | | As categorias usam nomenclatura interna da QC, com vocabulário próprio, e que modelos genéricos não conhecem. Com essa necessidade, CLU (Conversational Language Understanding) ou Custom Vision permite treinar com os rótulos proprietários. |
| Gerar descrição de produto a partir da foto + specs | | | ✅ | Requer raciocínio criativo e síntese multimodal (imagem + texto). LLM com visão (GPT-4o) é o único capaz de combinar os dois inputs e gerar texto coerente e persuasivo. |
| Transcrever áudio de atendimento em PT-BR | ✅ | | | Speech to Text pronto tem excelente performance em PT-BR com modelos pré-treinados no idioma. |
| Extrair CPF, e-mail, telefone de chat (LGPD) | ✅ | | | PII Detection do Azure Language é otimizado para entidades pessoais estruturadas (CPF, e-mail, telefone) e suporta PT-BR nativamente. Mais barato e mais seguro que usar LLM para PII. |
| Responder pergunta aberta do cliente sobre política de troca | | | ✅ | Perguntas abertas exigem compreensão de intenção e geração de resposta contextualizada. LLM + RAG (com os documentos de política da QC no AI Search) é o padrão correto. |
| OCR de etiqueta nutricional | ✅ | | | Read API (Vision) extrai texto de imagens com alta precisão para textos impressos estruturados. Mais barato e mais rápido que usar LLM para OCR puro. |
| Identificar peças industriais da empresa em foto de estoque | | ✅ | | Peças industriais específicas da QC não estão em nenhum modelo genérico. Custom Vision treinado com imagens rotuladas internamente é necessário para esse vocabulário visual proprietário. |

 
---

 
### Exercício 1.2 — Calcule o custo mensal

A Quantum Commerce processa por mês:

- **2M de reviews** para análise de sentimento (média 200 chars cada → 400M chars)
- **50.000 horas de atendimento** transcritas (Speech)
- **500k imagens de produto** analisadas (Vision)

Use a [calculadora Azure](https://azure.microsoft.com/pricing/calculator) e preencha:

| Serviço | Volume | Preço unit. (S0) | Total mensal |
|---------|--------|-----------------|--------------|
| Language (sentiment + entities) | 400M chars | ~$2/1M chars | **$800** |
| Speech batch (PT-BR) | 50.000h | ~$1/hora | **$50.000** |
| Vision Read + Tags | 500.000 chamadas | ~$1,50/1k | **$750** |
| **Total** | | | **$51.550/mês** |



**Análise:**

**a) Qual serviço pesa mais no orçamento mensal?**

Speech domina com $50.000/mês (97% do custo total). 
50k horas de transcrição batch é um volume enorme, chegando a equivaler a ~1.7 horas de áudio por dia. 

O que precisa acontecer na prática, é a QC avaliar se precisa transcrever 100% das chamadas ou apenas uma amostra representativa para análise de qualidade.
 
 

**b) Se substituir Sentiment pela Azure OpenAI (GPT-4o-mini @ ~$0.15/1M input + $0.60/1M output), quanto custaria? (Considere ~50 input tokens + 10 output tokens por review):**




Por review: ~50 tokens input + 10 tokens output

Custo por review:
input:  (50 × $0,15/1M) 
output: (10 × $0,60/1M)

Cálculo:
        Custo input + Custo output
        (50 × $0,15/1M) + (10 × $0,60/1M)
        $0,0000075 + $0,000006 
        $0,0000135/review

Se a QC processa 2M de reviews por mês:
Total 2M reviews: 2.000.000 × $0,0000135 = $27/mês



Comparado com Language API que gasta ~ $800/mês , **LLM é 30x mais barato** para sentimento avaliando o volume considerado.
Eu esperava uma resposta diferente, mas avaliando que o Language API cobra por caractere e o review com 200 chars (cálculo: ~$2/1M chars x 400 chars = $800).
Já o GPT-4o-mini cobra por token e é muito mais eficiente para textos curtos.




 
**c) Em que cenário vale a pena trocar API pronta por LLM mesmo sendo mais caro?**

Vale a pena quando a qualidade e riqueza da saída justificam o custo extra, por exemplo:

- Quando o vocabulário da QC é muito específico, com vocabulário próprio e que modelos genéricos não conhecem. A API pronta erra sistematicamente nas entidades do catálogo.
- Em contextos de decisão crítica, por exemplo a review que pode gerar recall de produto ou crise de reputação, a qualidade do LLM justifica o custo premium.
- O LLM pode retornar aspectos específicos, resumo contextualizado, ação recomendada e tom em uma única chamada, com API pronta exigiria de 3 a 4 chamadas separas para o mesmo resultado (sentiment + opinion mining + summarization + PII).

---

 
### Exercício 1.3 — Segurança: como sua Function autentica no AI Services
 
Marque a estratégia recomendada para produção e justifique:

| Estratégia | Recomendado? | Razão |
|-----------|--------------|-------|
| API Key hardcoded em `function_app.py` | **NÃO** | É um anti-padrão e uma vez que o repositório vai para o git no primeiro commit, é possível recuperar mesmo excluindo depois. Qualquer fork ou clone histórico expõe a credencial. |
| API Key como Application Setting da Function |  **Não ideal** | Sair do código melhora, mas qualquer usuário com acesso Contributor ao portal Azure vê o valor. Essa estratégia é aceitável apenas em ambiente de desenvolvimento. |
| API Key no Key Vault, lida pela Function via MI no Vault | **OK didático** | Elimina a chave do código, mas overhead desnecessário já que AI Services já suporta MI direta. |
| Token AAD via Managed Identity diretamente no AI Services | ✅ **Padrão produção** | A Function usa MI para obter token e se autentica direto no AI Services. Sem chave nenhuma em código, config ou Vault. |
 

**Pergunta extra:** Para o último caso (MI direta), quais são os 2 pré-requisitos no recurso AI Services para que funcione? (Dica: subdomínio + role)

1. **Custom subdomain habilitado:** o recurso `azurerm_cognitive_account` precisa de `custom_subdomain_name` configurado. 
Sem ele, o endpoint customizado não funciona.

2. **Role assignment `Cognitive Services User`:** a Managed Identity da Function precisa ter essa role no escopo do recurso AI Services. 
Sem ela, o token AAD é válido mas não tem permissão para chamar as APIs.


Na prática que fizemos nos labs, usamos MI direta em Storage e o mesmo padrão se aplica em AI Services.
Sem o custom subdomain, o SDK não consegue fazer a autenticação AAD, mesmo com a role configurad de forma correta.

No terraform, sem a configuração abaixo a MI funciona, mas retorna erro 403
role_definition_name = "Cognitive Services User"

 
 
---
 
### Exercício 1.4 — Vision capabilities map

Para cada cenário da QC, marque qual capacidade do Vision usar (**Tags**, **OCR (Read)**, **Object Detection**, **Caption**, **Image Embedding**, **Custom Vision**):
 
| Cenário | Capacidade | Justificativa |
|---------|-----------|---------------|
| Auto-categorizar produto novo enviado pelo vendedor | **Tags** | Retorna rótulos semânticos genéricos que a gente mapeia para as categorias do catálogo. Não precisa treinar nada. |
| Encontrar produtos visualmente similares ao da busca | **Image Embedding** | Gera um vetor da imagem, busca por similaridade de cosseno no AI Search. É base do RAG visual. |
| Detectar quantos produtos estão na prateleira de uma loja física | **Object Detection** | As tags só classificam, para contar e localizar cada item na foto precisa de bounding boxes, onde entra o Object Detection. |
| Extrair preço da etiqueta de um produto fotografado | **OCR (Read API)** | Extrai texto de imagens com alta precisão, texto impresso na etiqueta. Read API suporta textos impressos e manuscritos, incluindo números e símbolos de moeda, é simples e barato. |
| Gerar texto alternativo (alt-text) para acessibilidade | **Caption** | Gera uma frase descrevendo a imagem, muito usada em acessibilidade. |
| Identificar se a foto tem 1 ou mais pessoas (anonimização LGPD) | **Object Detection** (ou Face API) | Object Detection identifica presença de pessoas na imagem. Para LGPD, o objetivo é detectar e anonimizar rostos antes de publicar. FaceAPI é mais precisa para isso, mas o Object Detection também funciona caso não tenha intenção de habilitar mais um serviço. |
| Classificar entre os 12 modelos próprios da linha "QC Premium" | **Custom Vision** | Os 12 modelos exclusivos da QC não existem em nenhum modelo genérico de Vision. Sem treino customizado o Custom Vision genérico não tem como reconhê-los. |
 


---

## 🟡 Nível 2 — Intermediário: Pipeline e Decisões

---

### Exercício 2.3 — Quando treinar modelo próprio?

A Quantum Commerce está decidindo entre Vision pronto vs Custom Vision para classificar imagens de produtos.

**Dados:**

- 5M de SKUs, organizados em 150 categorias específicas da QC (ex: "sofá-3-lugares-modular", "tapete-shaggy-redondo")
- 90% das imagens são em fundo branco padronizado
- Para cada categoria existem ~30-50 imagens rotuladas internamente
- Volume de classificação: 50k imagens/mês

**Sua tarefa:**

### a) Calcule o custo mensal das 2 abordagens:
   - **Vision pronto + LLM para mapear tags genéricas → categoria QC:** Vision $0.0015 × 50k + GPT-4o-mini $X
   - **Custom Vision treinado:** treino inicial + storage + predição

Partindo da [calculadora Azure](https://azure.microsoft.com/pricing/calculator) e do pricing do OpenAI para fazer os cálculos.
Considerando o volume basse de 50K imagens/mês


**Vision pronto + LLM para mapear tags → categoria QC:**
Vision $0.0015 × 50k + GPT-4o-mini $X

Considerando que o Vision será usado apenas para extrair as tags genéricas e depois chamar o GPT-4o-mini para traduzir as tags para a categoria interna da QC.
Custo do Vision (Tags API): 

50.000 chamadas × $1,50 / 1.000 = $75/mês


Usando o GPT-4o-mini (uma chamada por imagem para mapeamento das tags):
 ~100 tokens input para tags + prompt
    - tags do Vision
    - lista das categorias no prompt
    - instrução do prompt


 ~20 tokens output por chamada para retornar o nome da categoria


Fazendo o cálculo:
Input: 50.000 × 100 tokens x $0,15/1M = $0,75
Output: 50.000 × 20 tokens x $0,60/1M = $0,60

Total LLM = $1,35/mês
Se serão $75/ mês de Custo do Vision + LLM para mapear as tags = 
**Custo Final Total da Opção 1: $76,35/mês**


**Custom Vision treinado:** treino inicial + storage + predição
O custo que vai aparecer na fatura para esse item: 
Treino: gratuit no S0
Storage: incluso
Predição: 50K x $2/1000 = $100/mês

Rotular as imagens de treino não entra na calculadora.
Considerando 150 categorias e 40 imagens, tem um total de 6.000 imagens a serem rotuladas antes do treinamento
Chegando a ~200h de esforço, ou seja, praticamente um mês de trabalho humano sem utilização de códigos.

Se considerar que pode aumentar as categorias a longo prazo o cálculo pode mudar completamento. Gerando ainda mais esforços e custo que não são demostrados na calculadora da fatura e isso vale a pena considerar.



| | Opção 1 (Pronto + LLM) | Opção 2 (Custom Vision) |
|---|---|---|
| Custo mensal | ~$76/mês | ~$100/mês |
| Custo de setup inicial | $0 | Esforço de rotulagem (~30-50 imagens por 150 categorias) |
| Custo de manutenção trimestral | Ajustar o prompt | ~20 novas categorias que evivale a ~800 imagens novas para rotulagem |



### b) Compare em termos de **qualidade esperada** — qual cobre melhor o vocabulário específico?

**Vision pronto + LLM:**
A qualidade estimada de acurácia por categorias dintintas é de ~70/80% , mas de categorias similares cai para ~50%
Considerando que o Vision possui tags genéricas, não conhecendo a taxonomia da QC e o LLM consegue mapear tags genéricas por categoria, mas com imprecisão das categorias que forem muito similares entre si.



**Custom Vision:**
A qualidade estimada de acurácia é de ~90% para todas as categorias.
Considerando que para esse caso a vantagem é clara, pois o modelo é treinado exatamente com as imagens do catálogo da QC, considerando fundo branco padronizado que são as condições ideais para visão computacional. O único problema que deixa em 90% serão as categorias com poucas imagens, que no início terão alguns casos.




### c) Compare em **manutenção:** como cada um se comporta quando a QC adiciona 20 novas categorias por trimestre?


**Vision pronto + LLM:**
Para essa situação, o Vision pronto com a LLM é o que mais se destaca.
Porque adicionar nova imagens, significa apenas que terá ajuste no prompt com novos nomes, sendo poucos minutos de trabalho e sem a necessidade de retreino e sem coletas de imagens.

O único risco que pode existir é que conforme a taxonomia da QC vai crescendo e ficando mais específica, o LLM vai começar a confundir categorias similares com mais frequência. Não é um problema no início, mas pode virar dor de cabeça quando tiver o dobro de imagem, por exmeplo.


**Custom Vision:**
Para essa situação, exige coletar e rotular mais 800 imagens, retreinar e validar.
O retreino é rápido, mas o gargalo smepre será a rotulagem humana e o banco de imagens rotuladas vai crescer sem parar, começando com 6.000 imagens e depois de 4 ciclos pode chegar a mais de 9.000 imagens rotuladas.

No longo prazo, o Custom Vision precisa de atenção, pois fica quase impossível de replicar e com depedência humana. Se alguém parar a rotulagem, o modelo não evolui.



d) Faça uma **recomendação justificada** considerando custo + qualidade + manutenção. Se possível, proponha uma arquitetura **híbrida** (ex: Custom para os 20 top vendedores + Pronto para o resto).


Considerando arquitetura híbrida:
Recomendo 2 camadas, onde:

_ Camada 1: Custom Vision para as top 30 categorias, considerando pareto representa 70% do volume de imagens da QC. 
Aqui vale o esforço de rotulagem porque é onde o impacto é maior. Estimando 30 categorias x 40 imagens, chegando a ~1.200 imagens para rotular, considerado rotulagem inicial viável.

Custo camada 1: 35k predições/mês × $2/1.000 = $70/mês


_ Camada 2: Vision pronto + LLM para os 30% restante, sendo 120 categorias e ~15K imagens /mês, cobrindo a longo prazo o custo de rotulagem das imagens adicionais.

Custo camada 2: 15k × $1,50/1.000 (Vision) + ~$0,60 (LLM) = $23/mês


O roteamento fica em uma Function para verficar se a categoria prevista está ou não no top 30. E gerencia se passa entre camada 1 ou se vai para a camada 2.
Custo híbrido total: $93/mês. Ou seja, mais barato que usar o Custom Vision puro ($100/mês) e com qualidade superior nas top categorias de maior volume.


O ideal é conforme longo prazo, avaliar as categorias por volume e importância e migrar as de mais impacto para o Custom Vision.
Considerando que a arquitetura é um MVP, e o mais correto para aprendizado, velocidade e custo. 
Mas entendendo que é MVP e não produto final.


--- 


## 🔴 Nível 3 — Avançado: Embeddings Reais e LLMs
