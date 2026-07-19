# Pendências — Entrega Aula 04 (Grupo 08)

> Checklist do que falta para a entrega ficar **100%**. Marque `[x]` conforme concluir.
> Base: `entregas/entrega-04/INSTRUCOES.md` + `aulas/04-servicos-cognitivos/exercicios.md`.
> Estado atual da pasta: só existem `respostas-pessoa1-aula04.md` e `respostas-pessoa3-aula04.md`.

## Divisão (referência)

- **Pessoa 1 — Tatiana:** N1 completo (1.1–1.4) + N2 2.3 (Vision vs Custom Vision) + N3 3.2 (Custom Vision)
- **Pessoa 2 — Luciana:** N2 2.1 (pipeline de reviews) + N3 3.1 (embeddings Azure OpenAI)
- **Pessoa 3 — Lucas:** N2 2.2 (casos de Speech) + N3 3.3 (sumarização via LLM)

---

## 🔴 Bloqueadores críticos (sem isto o ZIP não fecha / partes não rodam)

- [ ] **Consolidar o `entrega-grupo-aula04.md`** (documento principal do ZIP) a partir dos 3 `respostas-pessoaN`. Usar `entregas/template-entrega-grupo.md`. **Hoje não existe.**
- [ ] **Terraform `gpt-4o-mini`:** o exemplo do 3.1 só provisiona `text-embedding-3-small`. A rota 3.3 (Lucas) precisa de um deployment de **chat**. Adicionar `azurerm_cognitive_deployment "gpt-4o-mini"` no mesmo `azurerm_cognitive_account.openai`. **(dono: Pessoa 2, dependência do Lucas)**
- [ ] **Roles da Managed Identity no AI Services / OpenAI:**
  - `Cognitive Services User` (Language/Vision) para a MI da Function
  - `Cognitive Services OpenAI User` para a MI da Function (necessário para o 3.3)
  - `custom_subdomain_name` habilitado nos `azurerm_cognitive_account` (pré-requisito de MI — Ex. 1.3)
- [ ] **Pasta `function/`** com o `function_app.py` evoluído compartilhado (base 2.1 + rota 3.3). **Hoje não existe.**
- [ ] **Pasta `terraform/`** com o `main.tf` evoluído (AI Services + Key Vault + Function + roles + Azure OpenAI). **Hoje não existe.**

---

## 📦 Deliverables compartilhados do ZIP (INSTRUCOES.md)

- [ ] `entrega-grupo-aula04.md` (principal — ver bloqueadores)
- [ ] `README.md` — como rodar o pipeline (deploy + `curl` de cada rota, incl. `/sumarizar-reviews-produto`)
- [ ] `terraform/` — main.tf evoluído
- [ ] `function/` — function_app.py com rotas adicionais
- [ ] `scripts/` — re-indexação com embeddings (do 3.1)
- [ ] `diagramas/arquitetura-qc-aula04.png` — QC atualizada com camada cognitiva (Speech/Language/Vision)
- [ ] Anexar no doc principal: 3 reviews processadas (schema completo, do 2.1), JSON de análise de imagem (Vision), print do dashboard do Custom Vision (3.2)
- [ ] **Reflexão coletiva** ao final do doc principal (1 pt — Critério 5)
- [ ] Cabeçalho do grupo + distribuição do trabalho (1 pt — Critério 4)
- [ ] Gerar o ZIP `entrega-grupo-08-aula04.zip` e fazer upload no Portal FIAP (1 pessoa só)
- [ ] Conferir que o ZIP **NÃO** inclui: `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`, binários > 5 MB, chaves de API

---

## 👤 Pessoa 1 — Tatiana (N1 + 2.3 + 3.2)

- [x] 1.1 Pronto vs Custom vs LLM (feito no `respostas-pessoa1-aula04.md`)
- [ ] 1.2 Custo mensal (Language + Speech + Vision) — tabela + itens a/b/c
- [ ] 1.3 Segurança MI vs API key + os 2 pré-requisitos (subdomínio + role)
- [ ] 1.4 Vision capabilities map
- [ ] 2.3 Vision pronto vs Custom Vision (custo, qualidade, manutenção, recomendação híbrida)
- [ ] 3.2 Custom Vision: criar projeto, treinar, publicar, **print do dashboard**, URL da prediction API, custo 50k/mês
- [ ] Corrigir a tabela de distribuição do `respostas-pessoa1-aula04.md` (linha da Pessoa 2 está com nome em branco `** **`)

## 👤 Pessoa 2 — Luciana (2.1 + 3.1)

- [ ] 2.1 Pipeline robusto de reviews: summarization extractive + PII redaction + opinion mining + persistência no Cosmos (schema do enunciado)
- [ ] 2.1 Código atualizado no `function_app.py` + **3 exemplos de reviews processadas** no doc
- [ ] 3.1 Terraform: `azurerm_cognitive_account "openai"` + deployment `text-embedding-3-small` (região `eastus2`/`swedencentral`)
- [ ] 3.1 Script Python: lê 20 produtos do Blob, gera embeddings, re-indexa AI Search (`content_vector` 1536), roda 3 queries
- [ ] 3.1 Comparação vector vs semantic search + custo dos 5M produtos + estratégia de atualização incremental
- [ ] **Expor no Cosmos** o container `reviews` com o schema do 2.1 (`texto_redacted`, `sentimento_label`, `aspectos`) — **o 3.3 do Lucas lê daqui**

## 👤 Pessoa 3 — Lucas (2.2 + 3.3) — SUA PARTE

- [x] 2.2 Casos de Speech (3 casos, itens a–f) — feito e completo no `respostas-pessoa3-aula04.md`
- [x] 3.3 Código da rota `/sumarizar-reviews-produto` — escrito, sintaxe validada (`py_compile`) e lógica pura testada
- [x] 3.3 Comparação LLM vs Language API + custo dos 5M produtos
- [ ] **Merge da rota 3.3 no `function_app.py` compartilhado** — só possível depois do 2.1 (Pessoa 2) estar commitado
- [ ] Confirmar com a Pessoa 2: schema do Cosmos `reviews` bate com a query do 3.3
- [ ] Confirmar com a Pessoa 2: deployment `gpt-4o-mini` no Terraform + role `Cognitive Services OpenAI User`
- [ ] (Opcional) Validar a rota end-to-end no Azure após deploy — `curl "/api/sumarizar-reviews-produto?produto_id=5"`

---

## ✅ Validação final (antes de gerar o ZIP)

- [ ] `terraform validate` / `terraform plan` sem erros
- [ ] Deploy no Azure e teste de **cada rota** por `curl` (produtos, frete, sentimento/2.1, sumarização/3.3)
- [ ] Reviews aparecem enriquecidas no Cosmos (2.1) e o 3.3 consegue lê-las
- [ ] Embeddings re-indexados no AI Search (3.1) e queries retornando (3.1)
- [ ] Custom Vision publicado e testado via REST (3.2)
- [ ] Diagrama atualizado com a camada cognitiva
- [ ] Reflexão coletiva escrita
- [ ] ZIP gerado, conferido (`unzip -l`) e enviado no Portal FIAP
