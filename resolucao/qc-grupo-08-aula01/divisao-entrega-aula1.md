# Divisão da Entrega — Aula 1 (Fundamentos & IaC)

> Plano de divisão do trabalho da **Entrega 01** em **3 partes equilibradas** — uma por pessoa.
> Objetivo: cada integrante assume um bloco com peso semelhante, cobrindo **100% do obrigatório (N1 + N2)** e **todo o bônus N3** para maximizar a nota.

---

## 1. Contexto da entrega

| Item | Detalhe |
|------|---------|
| **Vale** | 10% da nota final (10 pts na rubrica) |
| **Prazo** | até 1 dia antes da Aula 2 |
| **Formato** | 1 ZIP por grupo no Portal FIAP (`entrega-grupo-NN-aula01.zip`) |
| **Quem envia** | apenas 1 membro faz o upload (combinar antes) |
| **Documento principal** | `entrega-grupo-aula01.md` (usar o [template obrigatório](../../entregas/template-entrega-grupo.md)) |

**Fontes:**
- Enunciado dos exercícios: [aulas/01-fundamentos-iac/exercicios.md](../../aulas/01-fundamentos-iac/exercicios.md)
- Instruções da entrega: [entregas/entrega-01/INSTRUCOES.md](../../entregas/entrega-01/INSTRUCOES.md)
- Rubrica: [entregas/rubrica.md](../../entregas/rubrica.md)
- Código base do N3: [aulas/01-fundamentos-iac/lab/terraform/](../../aulas/01-fundamentos-iac/lab/terraform/)

---

## 2. O que compõe a nota (mapa de pontos)

| Bloco | Exercícios | Obrigatório? | Pontos |
|-------|-----------|--------------|--------|
| 🟢 **N1 — Fundamentos** | 1.1, 1.2, 1.3, 1.4 | ✅ Sim | 3 pts (Critério 1) |
| 🟡 **N2 — Projeto Quantum Commerce** | 2.1 (+ diagrama), 2.2, 2.3 | ✅ Sim | 3 pts (C2) + 2 pts qualidade técnica (C3) |
| 🔴 **N3 — IaC avançado** | 3.1, 3.2, 3.3 | 🎁 Bônus | até +2 pts extras |
| 📋 Cabeçalho + distribuição | — | ✅ Sim | 1 pt (Critério 4) |
| 💭 Reflexão coletiva | — | ✅ Sim | 1 pt (Critério 5) |

> **Teto da entrega: 10 pts.** O bônus do N3 pode compensar perdas em outros critérios.
> Os 3 níveis são **divisão de trabalho dentro do grupo**, não escolha individual livre.

## Distribuição do trabalho

| Membro                  | Nível assumido          | Item específico                                                                |
|-------------------------|-------------------------|--------------------------------------------------------------------------------|
| Tatiana Mastrogiovanni  | 🟢 N1 + 🔴 N3 (bônus)  | Exercícios 1.1, 1.2, 1.3, 1.4 + 3.3 (multi-cloud)                              |
| Luciana Chaves D'Olivo  | 🟡 N2 + coordenação    | Exercício 2.1 (arquitetura + diagrama) + 2.3; montagem do doc, reflexão e ZIP  |
| Lucas Marujo Amadeu     | 🟡 N2 + 🔴 N3 (bônus)  | Exercício 2.2 (custos) + 3.1 (Terraform) + 3.2 (Bicep)                         |

---

## 3. A divisão em 3 partes

A lógica da divisão é dar a cada pessoa um **bloco coeso e com sinergia interna**, de peso parecido:

- **Pessoa A** → todo o N1 (conceitual) + a análise estratégica multi-cloud do N3 (que conversa com os fundamentos).
- **Pessoa B** → o coração do projeto QC: arquitetura + diagrama + estratégia de migração + liderança da reflexão e do empacotamento do ZIP.
- **Pessoa C** → a trilha "números e infraestrutura": comparativo de custos + as duas tarefas de IaC do N3 (Terraform e Bicep, que são naturalmente a mesma coisa traduzida).

### Quadro-resumo

| | **Pessoa A — Fundamentos & Estratégia** | **Pessoa B — Arquitetura QC & Coordenação** | **Pessoa C — Custos & IaC** |
|---|---|---|---|
| **Nível principal** | 🟢 N1 | 🟡 N2 | 🟡 N2 + 🔴 N3 |
| **Exercícios** | 1.1, 1.2, 1.3, 1.4 + **3.3** | 2.1 (+ diagrama), 2.3 | 2.2 + **3.1**, **3.2** |
| **Bônus N3** | 3.3 (multi-cloud) | — | 3.1 (Terraform) + 3.2 (Bicep) |
| **Tarefas de coordenação** | revisar respostas de C | montar o documento, **liderar reflexão**, gerar e enviar o ZIP | conferir o diff do `terraform plan` |
| **Peso estimado** | ~11 | ~11 | ~12 |

> O peso é dado em "pontos de esforço" relativos (não em nota). A diferença é pequena e proposital: a Pessoa C concentra as duas tarefas de IaC porque **3.2 é literalmente traduzir o resultado de 3.1** — fazer as duas junto é mais rápido do que dividir.

---

## 4. Detalhe de cada parte

### 🟢 Pessoa A — Fundamentos & Estratégia (N1 completo + 3.3)

**Entregáveis:**

| Exercício | O que fazer | Dica |
|-----------|-------------|------|
| **1.1** Modelos de serviço | Classificar 9 serviços em IaaS/PaaS/SaaS/FaaS + 1 frase de justificativa cada | Há gabarito no enunciado — entenda o porquê, não só copie |
| **1.2** Os 6 Rs | Escolher o R certo para os 5 cenários (A–E) e justificar | Gabarito parcial no fim do `exercicios.md` |
| **1.3** SLA | a) downtime/ano; b) impacto em R$; c) SLA mínimo p/ < R$ 50k/ano | Use as fórmulas dadas; gabarito numérico no enunciado |
| **1.4** RBAC | Mapear 5 perfis → role built-in do Azure + justificativa | Princípio do **menor privilégio**; role escoped no RG, nunca Owner |
| **3.3** Multi-cloud (🎁 bônus) | a) arquitetura 2+ nuvens; b) 4 desafios; c) Terraform × Pulumi; d) custo de egress 10 TB/mês Azure↔AWS | Conecta com o que você já dominou em 1.1/1.2; pesquise Azure Arc e AWS Outposts |

**Por que esse agrupamento:** o N1 inteiro é conceitual e flui de um exercício para o outro (modelos → migração → SLA → segurança). O **3.3** é a continuação natural dessa linha estratégica (decisão de provedor, lock-in, custo), então quem dominou o N1 escreve o 3.3 com o mesmo vocabulário.

**Tarefa extra:** revisar a tabela de custos da Pessoa C (segundo par de olhos nos números).

---

### 🟡 Pessoa B — Arquitetura QC & Coordenação (2.1 + 2.3 + ZIP)

**Entregáveis:**

| Exercício | O que fazer | Dica |
|-----------|-------------|------|
| **2.1** Arquitetura QC | 1) camadas; 2) provedor principal + porquê; 3) tabela de serviços (Azure/AWS/GCP) por categoria; 4) **diagrama** | Diagrama no Excalidraw / draw.io / foto — **sem instalar nada**. É o embrião que evolui até a Aula 6 |
| **2.3** Estratégia de migração | a) descrever um workload real (genérico); b) qual dos 6 Rs; c) serviço Azure + estimativa mensal; d) maior obstáculo | Aproveite os 6 Rs revisados pela Pessoa A |

**Tarefas de coordenação (valem ponto no Critério 4 e 5):**
- Montar o `entrega-grupo-aula01.md` a partir do [template](../../entregas/template-entrega-grupo.md) e colar as partes de todos.
- **Liderar a reflexão coletiva** (3–5 parágrafos): aprendizado + conexão com arquitetura agentic + o que fariam diferente. Recolher 1 frase de cada integrante.
- **Gerar o ZIP** e fazer o upload no Portal FIAP.

**Por que esse agrupamento:** o **diagrama é o item de maior peso visual** e é o núcleo do projeto QC; concentrá-lo com a estratégia de migração (2.3) mantém a "visão de produto" numa pessoa só. Como ela já está consolidando o documento, faz sentido que também lidere a reflexão e o empacotamento.

> ⚠️ O **diagrama é parte obrigatória da entrega** (`diagramas/arquitetura-qc-aula01.png`). Sem ele, o N2 perde pontos.

---

### 🔴 Pessoa C — Custos & IaC (2.2 + 3.1 + 3.2)

**Entregáveis:**

| Exercício | O que fazer | Dica |
|-----------|-------------|------|
| **2.2** Comparativo de custos | Preencher a tabela Azure/AWS/GCP (2 VMs, 500 GB storage, banco gerenciado, 10M req serverless) + responder a/b/c | Use as 3 calculadoras oficiais (links no enunciado); aplicar Reserved Instances no item b |
| **3.1** Terraform (🎁 bônus) | Endurecer o NSG do lab: SSH só do seu IP (`var.meu_ip` + `/32`), 2ª subnet `subnet-app 10.0.2.0/24`, output do IP público, `plan` sem recriar a VM | Base em [lab/terraform/main.tf](../../aulas/01-fundamentos-iac/lab/terraform/main.tf). Tudo no Cloud Shell, `destroy` ao final |
| **3.2** Bicep (🎁 bônus) | Traduzir o `main.tf` para `main.bicep` (ou `bicep decompile`), deployar, comparar nº de linhas ARM × TF × Bicep e responder qual é mais legível | `bicep` já vem no Cloud Shell. `az group delete` ao final |

**Tarefa extra:** documentar no `README.md` como rodar o N3 (comandos `terraform`/`az` e o `destroy`/`delete` de limpeza).

**Por que esse agrupamento:** **3.1 e 3.2 são a mesma infraestrutura** — primeiro você endurece em Terraform, depois traduz para Bicep e compara. Fazer as duas seguidas elimina retrabalho. O comparativo de custos (2.2) é "trilha de números" e fecha bem com o perfil técnico/infra dessa pessoa. É a parte ligeiramente mais pesada, por isso ela não pega tarefas de coordenação.

---

## 5. Por que essa divisão é justa e equilibrada

1. **Carga parecida** — cada pessoa fica com ~11–12 pontos de esforço; a Pessoa C tem um pouco mais de IaC, compensado por **não** ter tarefas de coordenação (montar documento, reflexão, ZIP, que ficam com a Pessoa B).
2. **Cobertura total** — N1 e N2 (obrigatórios) 100% cobertos **e** todo o N3 (bônus) distribuído → grupo joga para os **+2 pts extras**.
3. **Sinergia interna** — ninguém troca de contexto à toa: A fica no conceitual/estratégico (N1 + 3.3), B na visão de produto (arquitetura + diagrama + reflexão), C na infra/números (custos + Terraform + Bicep).
4. **Revisão cruzada** — A revisa os custos de C; B consolida e revisa tudo ao montar o documento → reduz erro e evita "free rider" (Critério 4).
5. **Rastreabilidade** — a tabela da seção 6 vai pronta no cabeçalho da entrega, que é a **única evidência da divisão** usada na correção.

> 💡 **Rodízio (Critério 4):** quem fez 🟢 N1 nesta aula (Pessoa A) deve preferencialmente assumir 🟡 N2 ou 🔴 N3 na **próxima** entrega. Anote isso para a Aula 2.

---

## 6. Tabela pronta para o cabeçalho da entrega

Cole isto na seção **"Distribuição do trabalho"** do `entrega-grupo-aula01.md` (substitua os nomes):

```markdown
## Distribuição do trabalho

| Membro    | Nível assumido        | Item específico                                  |
|-----------|-----------------------|--------------------------------------------------|
| Tatiana Mastrogiovanni Haddad            | 🟢 N1 + 🔴 N3 (bônus) | Exercícios 1.1, 1.2, 1.3, 1.4 + 3.3 (multi-cloud) |
| Luciana Chaves D'Olivo            | 🟡 N2 + coordenação   | Exercício 2.1 (arquitetura + diagrama) + 2.3; montagem do doc, reflexão e ZIP |
| Lucas Marujo Amadeu | 🟡 N2 + 🔴 N3 (bônus) | Exercício 2.2 (custos) + 3.1 (Terraform) + 3.2 (Bicep) |
```

---

## 7. Checklist final antes do upload

- [X] N1 (1.1–1.4) respondido com justificativas — **Pessoa A**
- [X] N2: arquitetura + **diagrama PNG** em `diagramas/` — **Pessoa B**
- [X] N2: comparativo de custos preenchido — **Pessoa C**
- [X] N2: estratégia de migração (2.3) — **Pessoa B**
- [X] N3 (bônus): `terraform/` com `main.tf`, `variables.tf`, `outputs.tf` + `README.md` — **Pessoa C**
- [X] N3 (bônus): 3.2 Bicep e 3.3 multi-cloud documentados — **C e A**
- [X] Cabeçalho do grupo + tabela de distribuição preenchidos
- [X] Reflexão coletiva (3–5 parágrafos) — **Pessoa B consolida**
- [X] ZIP **não** contém `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`
- [X] Nome do ZIP: `entrega-grupo-08-aula01.zip`, pasta interna `qc-grupo-08-aula01/`
- [X] `terraform destroy` / `az group delete` executados (confirmado pelo Lucas)
- [ ] Upload feito por **1 só membro** no Portal FIAP

---

### Observação sobre o tamanho do grupo

Este plano assume **grupo de 3**. Se forem **4–5 pessoas**, mantenha os 3 blocos e use os membros extras como **apoio/revisão**: um 4º revisa o N3 e a qualidade do código (Critério 3), um 5º refina o diagrama e a reflexão. Cada membro precisa de **pelo menos uma contribuição** registrada.
