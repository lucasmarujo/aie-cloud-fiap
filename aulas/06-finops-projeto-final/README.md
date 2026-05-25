# Aula 6 — FinOps & Projeto Integrado Final

## Objetivos de aprendizagem

Ao final desta aula, você será capaz de:

- Explicar o que é **FinOps** e os três pilares: **Inform, Optimize, Operate**.
- Usar **Cost Management + Azure Advisor** para identificar desperdícios.
- Aplicar técnicas de otimização: reserved instances, spot, auto-scale, right-sizing, lifecycle policies.
- Aplicar FinOps especificamente a workloads de AI (tokens, embeddings, GPU, modelos idle).
- Estimar o custo mensal (TCO) da arquitetura cloud da QC via Pricing Calculator.
- **Consolidar o projeto integrado final** com suporte do professor.

---

## Formato da aula

A Aula 6 tem **2 partes**:

1. **FinOps (~1h50)** — T→L intercalados sobre os 3 pilares, Cost Management, técnicas de otimização e FinOps aplicado a AI.
2. **Trabalho assistido em grupo (~1h40)** — tempo guiado para consolidar o **Projeto Integrado Final**, com o professor circulando para tirar dúvidas e atender grupos com pendências.

**Não há apresentação oral.** O projeto integrado final é entregue como ZIP no Portal FIAP **1 semana após esta aula**.

---

## Projeto Integrado Final (50% da nota)

A entrega final consolida tudo o que foi construído nas Aulas 1-5 em **um único ZIP coerente**:

- Arquitetura cloud completa da QC (diagrama + ADRs)
- Terraform consolidado que provisiona TODA a infra
- Function com as 5 tools (`/produtos`, `/transcrever`, `/analisar-reviews`, `/analisar-imagem`, `/recomendar`)
- Tools-spec em JSON Schema (function calling)
- Análise FinOps (estimativa + propostas de otimização)
- Reflexão estratégica (roadmap 12 meses + lições aprendidas)

**Detalhes completos do entregável + cronograma + perguntas frequentes:** [entregas/projeto-final/INSTRUCOES.md](../../entregas/projeto-final/INSTRUCOES.md).

**Rubrica (50 pts):** [entregas/rubrica.md](../../entregas/rubrica.md) — seção "Rubrica do Projeto Integrado Final".

---

## Material da aula

> Em construção — disponível antes da aula.

- `lab/` — FinOps prático: Cost Management + Pricing Calculator aplicado à arquitetura QC
- `exercicios/` — Otimização de uma arquitetura dada (sem entrega ZIP separada — esta aula não tem entrega intermediária; a Aula 6 alimenta o projeto integrado final)

---

## Pré-requisitos

- Aulas 1 a 5 concluídas
- Projeto da Quantum Commerce em andamento (5 entregas intermediárias submetidas)
- Cada grupo já tem **arquitetura QC parcialmente definida** das entregas anteriores
- Repositório privado do grupo atualizado com material das Aulas 1-5
