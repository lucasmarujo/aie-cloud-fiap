# Divisão da Entrega — Aula 2 (Storage & Bancos de Dados)

> Plano de divisão do trabalho da **Entrega 02** em **3 partes equilibradas** — uma por pessoa.
> Objetivo: cada integrante assume um bloco coeso e de peso semelhante, cobrindo **100% do obrigatório (N1 + N2)** e **todo o bônus N3** para jogar pelos **+2 pts extras**.

---

## 1. Contexto da entrega

| Item | Detalhe |
|------|---------|
| **Vale** | 10% da nota final (10 pts na rubrica) |
| **Prazo** | até 1 dia antes da Aula 3 |
| **Formato** | 1 ZIP por grupo no Portal FIAP (`entrega-grupo-08-aula02.zip`) |
| **Quem envia** | apenas 1 membro faz o upload (combinar antes) |
| **Documento principal** | `entrega-grupo-aula02.md` (usar o [template obrigatório](../../entregas/template-entrega-grupo.md)) |

**Fontes:**
- Enunciado dos exercícios: [aulas/02-storage-bancos/exercicios.md](../../aulas/02-storage-bancos/exercicios.md)
- Instruções da entrega: [entregas/entrega-02/INSTRUCOES.md](../../entregas/entrega-02/INSTRUCOES.md)
- Rubrica: [entregas/rubrica.md](../../entregas/rubrica.md)
- Lab + código base (Terraform/Python): [aulas/02-storage-bancos/lab/](../../aulas/02-storage-bancos/lab/)

---

## 2. O que compõe a nota (mapa de pontos)

| Bloco | Exercícios | Obrigatório? | Pontos |
|-------|-----------|--------------|--------|
| 🟢 **N1 — Fundamentos** | 1.1, 1.2, 1.3, 1.4 | ✅ Sim | 3 pts (Critério 1) |
| 🟡 **N2 — Projeto Quantum Commerce** | 2.1 (matriz + diagrama), 2.2, 2.3 | ✅ Sim | 3 pts (C2) + 2 pts qualidade técnica (C3) |
| 🔴 **N3 — Vector search & Analytics** | 3.1, 3.2, 3.3 | 🎁 Bônus | até +2 pts extras |
| 📋 Cabeçalho + distribuição | — | ✅ Sim | 1 pt (Critério 4) |
| 💭 Reflexão coletiva | — | ✅ Sim | 1 pt (Critério 5) |

> **Teto da entrega: 10 pts.** O bônus do N3 pode compensar perdas em outros critérios.
> Os 3 níveis são **divisão de trabalho dentro do grupo**, não escolha individual livre.

---

## 3. A divisão em 3 partes

A lógica é dar a cada pessoa um **bloco com sinergia interna** (mesmo vocabulário, sem troca de contexto à toa) e peso parecido:

- **Pessoa A** → todo o N1 (conceitual: storage, tiers, relacional×NoSQL, RBAC) **+ 2.2** (plano de migração). É a "trilha fundamentos & estratégia": os fundamentos do N1 alimentam diretamente as decisões do plano de migração.
- **Pessoa B** → o coração do projeto QC: **2.1** (matriz de decisão dos 9 domínios + **diagrama**) **+ 2.3** (particionamento do Cosmos, que aprofunda um container que a própria matriz escolhe) + montagem do documento, reflexão e ZIP.
- **Pessoa C** → todo o **N3 bônus** (3.1 vector search + 3.2 Synapse + 3.3 benchmark). As três tarefas compartilham a **mesma infra** (AI Search, Cosmos, SQL, Blob), então fazê-las juntas elimina retrabalho de setup.

### Quadro-resumo

| | **Pessoa A — Fundamentos & Migração** | **Pessoa B — Arquitetura QC & Coordenação** | **Pessoa C — Vector Search & Analytics** |
|---|---|---|---|
| **Membro** | **Lucas Marujo Amadeu** | _(a definir)_ | _(a definir)_ |
| **Nível principal** | 🟢 N1 + 🟡 N2 (parcial) | 🟡 N2 | 🔴 N3 (bônus) |
| **Exercícios** | 1.1, 1.2, 1.3, 1.4 + **2.2** | 2.1 (+ diagrama), 2.3 | **3.1**, **3.2**, **3.3** |
| **Bônus N3** | — | — | 3.1 + 3.2 + 3.3 |
| **Tarefas de coordenação** | revisar a matriz (2.1) de B e os números do benchmark (3.3) de C | montar o documento, **liderar reflexão**, gerar e enviar o ZIP | documentar o `README.md` (como rodar scripts/terraform do N3) |
| **Peso estimado** | ~13 | ~13 | ~15 |

> O peso é dado em "pontos de esforço" relativos (não em nota). A Pessoa C concentra um pouco mais porque pega **todo o bônus** — compensado por **não** ter tarefas de coordenação (que ficam com a Pessoa B) e pela economia de fazer 3.1/3.2/3.3 sobre a mesma infra.

---

## 4. Detalhe de cada parte

### 🟢🟡 Pessoa A — Fundamentos & Migração (N1 completo + 2.2) — _Lucas Marujo Amadeu_

**Entregáveis:**

| Exercício | O que fazer | Dica |
|-----------|-------------|------|
| **1.1** Tipos de Storage | Classificar 6 cenários em Object / File / Block + 1 frase de justificativa cada | Há gabarito no enunciado — entenda o **porquê** (acesso, latência, montagem), não só copie |
| **1.2** Tiers de acesso (cálculo) | a) custo 100% Hot; b) custo com lifecycle 30d Hot + Archive; c) economia anual | Use $0,018/GB Hot e $0,002/GB Archive; 2 TB = 2.048 GB. Cuidado com a premissa de steady-state |
| **1.3** Relacional × NoSQL × Vector | Marcar o banco certo para 7 casos de uso da QC + justificar | Pense em esquema fixo×variável, ACID, TTL e busca semântica |
| **1.4** Key Vault & RBAC | Mapear 5 perfis → role built-in + justificativa | Princípio do **menor privilégio**; separar **plano de gestão** × **plano de dados** de segredos |
| **2.2** Plano de migração (12 meses) | a) 6 Rs por repositório; b) serviço Azure de destino; c) migrar sem downtime (DMS/AzCopy/Data Box); d) custo de egress dos 50 TB; e) LGPD | Aproveita os 6 Rs da Aula 1. **Atenção:** ingress no Azure é grátis — o "custo de saída" é uma pegadinha |

**Por que esse agrupamento:** o N1 inteiro é conceitual e flui de um exercício para o outro (storage → tiers → modelagem de banco → segurança). O **2.2** é a continuação natural: decidir *para onde* migrar cada repositório usa exatamente o vocabulário de tiers (1.2), de relacional×NoSQL (1.3) e de menor privilégio (1.4). Quem domina o N1 escreve o plano de migração com o mesmo raciocínio.

**Tarefa extra (Critério 4):** segundo par de olhos na **matriz 2.1** da Pessoa B (consistência das escolhas de serviço com o que o N1 defende) e nos **números do benchmark 3.3** da Pessoa C.

---

### 🟡 Pessoa B — Arquitetura QC & Coordenação (2.1 + 2.3 + ZIP)

**Entregáveis:**

| Exercício | O que fazer | Dica |
|-----------|-------------|------|
| **2.1** Matriz de decisão de dados | Preencher os **9 domínios** (Produtos, Clientes, Pedidos, Carrinhos, Reviews, Busca, Sessões, Histórico, Modelos ML) com serviço Azure + SKU + justificativa, e desenhar o **diagrama** da camada de dados | Esta é a **peça central** da entrega (C2). Diagrama no Excalidraw/draw.io → `diagramas/arquitetura-qc-aula02.png`. **Sem ele o N2 perde pontos** |
| **2.3** Particionamento Cosmos | a) por que `id`/`score`/`data` são más partition keys; b) o ponto fraco de `produto_id` (hot partition); c) hierarchical partition keys para "reviews de um cliente"; d) tamanho da partição de 50.000 reviews vs quota de 20 GB | Liga direto com a linha "Reviews → Cosmos" da matriz 2.1 |

**Tarefas de coordenação (valem ponto nos Critérios 4 e 5):**
- Montar o `entrega-grupo-aula02.md` a partir do [template](../../entregas/template-entrega-grupo.md) e colar as partes de todos.
- **Liderar a reflexão coletiva** (3–5 parágrafos): por que segregar segredos no Key Vault muda o modelo de segurança numa plataforma **agentic** (foco pedido na rubrica) + aprendizado + o que fariam diferente.
- **Gerar o ZIP** e fazer o upload no Portal FIAP.

**Por que esse agrupamento:** o **diagrama** é o item de maior peso visual e o núcleo do projeto QC; mantê-lo com o particionamento do Cosmos (2.3) concentra a "visão de arquitetura de dados" numa pessoa. Como ela já consolida o documento, faz sentido liderar reflexão e empacotamento.

> ⚠️ O **diagrama é parte obrigatória** (`diagramas/arquitetura-qc-aula02.png`). Deve mostrar a camada de dados completa: Blob (catálogo/imagens/logs) + SQL (T_PRODUTOS) + Cosmos (reviews) + AI Search (índice/RAG) + Key Vault (segredos).

---

### 🔴 Pessoa C — Vector Search & Analytics (N3 bônus completo)

**Entregáveis:**

| Exercício | O que fazer | Dica |
|-----------|-------------|------|
| **3.1** Vector search verdadeira | Gerar embeddings com `sentence-transformers` (all-MiniLM-L6-v2), criar índice com campo vector no AI Search, indexar os produtos, rodar 3 queries e **comparar** com o semantic search do lab + responder as 4 perguntas de reflexão | É o **bônus mais valorizado** (base do RAG). Tudo no Cloud Shell, `pip install --user`. Script pronto no enunciado |
| **3.2** Synapse Serverless | Criar `synapse.tf` (workspace + Data Lake Gen2 + firewall), gerar 3 CSVs de logs, subir ao Blob, rodar `OPENROWSET` no Serverless SQL Pool + responder as 3 reflexões | Storage precisa de `is_hns_enabled = true`. Reportar bytes processados na query |
| **3.3** Benchmark Cosmos × SQL × AI Search | Implementar as 3 versões da busca, medir latência de 10 queries, comparar qualidade e custo (1M queries/mês) e **recomendar** | Tabela comparativa + recomendação justificada. A recomendação fecha com a matriz 2.1 (B) e o N1 1.3 (A) |

**Tarefa extra:** documentar no `README.md` como rodar o N3 (comandos `terraform`/`az`/`python3`, variáveis de ambiente e o `terraform destroy` de limpeza). **Não commitar** `terraform.tfstate*`, `.env`, `__pycache__/`.

**Por que esse agrupamento:** 3.1, 3.2 e 3.3 rodam sobre a **mesma camada de dados** do lab (AI Search, Cosmos, SQL, Blob). Fazer as três em sequência reaproveita todo o setup (índices, role assignments, dados) e é mais rápido do que espalhar. É a parte ligeiramente mais pesada, por isso essa pessoa **não** pega tarefas de coordenação.

---

## 5. Por que essa divisão é justa e equilibrada

1. **Carga parecida** — ~13 / ~13 / ~15 pontos de esforço. A Pessoa C tem um pouco mais por concentrar **todo o bônus**, compensado por não ter coordenação (documento, reflexão, ZIP ficam com B) e pela economia de infra compartilhada no N3.
2. **Cobertura total** — N1 e N2 (obrigatórios) 100% cobertos **e** todo o N3 (bônus) distribuído → o grupo joga pelos **+2 pts extras**.
3. **Sinergia interna** — ninguém troca de contexto à toa: **A** no conceitual/estratégico (N1 → migração), **B** na arquitetura de dados (matriz + diagrama + particionamento + reflexão), **C** no código/infra avançada (vector search + Synapse + benchmark).
4. **Revisão cruzada** — A revisa a matriz de B e os números de C; B consolida e revisa tudo ao montar o documento → reduz erro e evita "free rider" (Critério 4).
5. **Rastreabilidade** — a tabela da seção 6 vai pronta no cabeçalho da entrega, **única evidência da divisão** usada na correção.

> 💡 **Rodízio (Critério 4):** na Aula 1, o Lucas (Pessoa A) ficou com 🟡 N2 + 🔴 N3. Aqui ele **rotaciona** para ancorar o 🟢 N1 + a parte estratégica do N2 (2.2). Registrar isso no cabeçalho reforça o ponto do Critério 4.

---

## 6. Tabela pronta para o cabeçalho da entrega

Cole isto na seção **"Distribuição do trabalho"** do `entrega-grupo-aula02.md` (preencher B e C quando definidos):

```markdown
## Distribuição do trabalho

| Membro              | Nível assumido            | Item específico                                                  |
|---------------------|---------------------------|------------------------------------------------------------------|
| Lucas Marujo Amadeu | 🟢 N1 + 🟡 N2 (parcial)   | Exercícios 1.1, 1.2, 1.3, 1.4 + 2.2 (plano de migração)          |
| _(a definir)_       | 🟡 N2 + coordenação       | Exercício 2.1 (matriz + diagrama) + 2.3; montagem do doc, reflexão e ZIP |
| _(a definir)_       | 🔴 N3 (bônus)             | Exercícios 3.1 (vector search) + 3.2 (Synapse) + 3.3 (benchmark) |
```

---

## 7. Checklist final antes do upload

- [ ] N1 (1.1–1.4) respondido com justificativas — **Pessoa A (Lucas)**
- [ ] N2: 2.2 plano de migração (6 Rs + serviços + sem downtime + egress + LGPD) — **Pessoa A (Lucas)**
- [ ] N2: matriz dos 9 domínios + **diagrama PNG** em `diagramas/` — **Pessoa B**
- [ ] N2: particionamento Cosmos (2.3) — **Pessoa B**
- [ ] N3 (bônus): vector search (3.1) + Synapse (3.2) + benchmark (3.3) — **Pessoa C**
- [ ] N3 (bônus): `terraform/` (+ `synapse.tf`) e `scripts/` com `README.md` de como rodar — **Pessoa C**
- [ ] Cabeçalho do grupo + tabela de distribuição preenchidos
- [ ] Reflexão coletiva (3–5 parágrafos, foco Key Vault numa plataforma agentic) — **Pessoa B consolida**
- [ ] ZIP **não** contém `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`
- [ ] Nome do ZIP: `entrega-grupo-08-aula02.zip`, pasta interna `qc-grupo-08-aula02/`
- [ ] `terraform destroy` executado ao final do lab (custo zero)
- [ ] Upload feito por **1 só membro** no Portal FIAP

---

### Observação sobre o tamanho do grupo

Este plano assume **grupo de 3**. Se forem **4–5 pessoas**, mantenha os 3 blocos e use os membros extras como **apoio/revisão**: um 4º revisa o N3 e a qualidade do código (Critério 3), um 5º refina o diagrama e a reflexão. Cada membro precisa de **pelo menos uma contribuição** registrada no cabeçalho.
