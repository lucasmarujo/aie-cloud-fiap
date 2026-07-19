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
| ** ** | 🟡 **N2 (parcial)** + 🔴 **N3 (parcial)** | N2 2.1 (pipeline reviews) + N3 3.1 (embeddings Azure OpenAI) |
| ** ** | 🟡 **N2 (parcial)** + 🔴 **N3 (parcial)**  | N2 2.2 (casos de Speech) + N3 3.3 (sumarização LLM) |



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