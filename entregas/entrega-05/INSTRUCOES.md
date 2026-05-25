# Entrega 05 — Aula 5 (MLOps na Nuvem)

**Vale:** 10% da nota final
**Prazo:** até 1 dia antes da Aula 6
**Onde:** upload de UM ZIP no Portal FIAP (combine no grupo quem faz)

> **Última entrega intermediária!** A Aula 6 é dedicada ao **trabalho assistido em grupo no projeto integrado final** (50% da nota, **entrega ZIP 1 semana após a aula, sem apresentação oral**) — ver [projeto-final/](../projeto-final/).

---

## ⚠️ Atenção custo

Se você fez o **Exercício N3.1 (Online Endpoint produtivo)** e deixou o endpoint ativo, **delete agora**:

```bash
az ml online-endpoint delete --name <seu-endpoint> --yes \
  -w <workspace> -g <rg>
```

Endpoint ativo custa ~$0,30/h ≈ $7/dia. O Critério 3 da rubrica **desconta** se o endpoint estiver ativo na hora da correção.

---

## O que entregar

| Item | Obrigatório? | Pontos máximos |
|------|--------------|----------------|
| Cabeçalho do grupo + distribuição do trabalho | ✅ Sim | 1 pt (Critério 4) |
| 🟢 N1 — Exercícios 1.1 (maturidade MLOps), 1.2 (param/metric/artifact), 1.3 (Registry + rollback), 1.4 (segurança ML) | ✅ Sim | 3 pts (Critério 1) |
| 🟡 N2 — 2.1 (documentação do pipeline MLOps + diagrama), 2.2 (5ª tool `/recomendar` na Function), 2.3 (plano de drift monitoring) | ✅ Sim | 3 pts (Critério 2) + 2 pts qualidade técnica (Critério 3) |
| 🔴 N3 — 3.0 (sweep job), 3.1 (Endpoint + load test), 3.2 (A/B testing), 3.3 (MLOps vs LLMOps) | 🎁 Bônus | até +2 pts extras |
| Reflexão coletiva ao final | ✅ Sim | 1 pt (Critério 5) |
| **Total** | | **10 pts** |

Conteúdo dos exercícios: [aulas/05-mlops/exercicios.md](../../aulas/05-mlops/exercicios.md).

> **Perfil dos alunos:** N1 e N2 são **conceituais e de operacionalização** — não exigem programação ML. N3 é para grupos com perfil avançado em ML.

---

## Estrutura do ZIP

Nome: `entrega-grupo-NN-aula05.zip`.

```
qc-grupo-NN-aula05/
├── entrega-grupo-aula05.md       # ⭐ documento principal (template em ../template-entrega-grupo.md)
├── README.md                     # Como rodar o pipeline
├── terraform/                    # ML Workspace + Compute Cluster (e endpoint se N3)
├── notebooks/                    # treinar_recomendador.py (treino local com tracking)
├── job/                          # train.py, job.yml, conda.yml, data-asset.yml (job reproduzível)
├── endpoint/                     # endpoint.yml, deployment.yml, request.json (se entregue)
└── diagramas/
    ├── pipeline-mlops-qc.png     # Diagrama do pipeline (N2.1)
    └── arquitetura-qc-aula05.png # QC atualizada com camada de ML
```

Anexar também no `entrega-grupo-aula05.md`:

- **Print** do experimento no Studio com métricas (`precision_at_k_proxy`)
- **Print** do Model Registry com `recomendador-qc` v1/v2/v3
- **Print** do endpoint funcionando ANTES de deletar (se N3.1 entregue)
- **JSON Schema** da tool `/recomendar` (se N2.2 entregue)
- **Resposta consolidada** ao diagnóstico de maturidade MLOps da QC (N1.1)

**NÃO incluir:** `terraform.tfstate*`, `.env`, `*.pem`, `__pycache__/`, `model_artifacts/*.pkl`, `outputs/*`. Endpoint key (chave de API) — **nunca commitar**.

---

## Como gerar e enviar

```bash
cd ~/qc-grupo-NN
git pull origin main
git archive --format=zip --prefix=qc-grupo-NN-aula05/ -o ~/entrega-grupo-NN-aula05.zip HEAD:aula05
unzip -l ~/entrega-grupo-NN-aula05.zip
```

Upload no Portal FIAP, tarefa "Entrega Aula 5".

---

## Critérios de avaliação

[Rubrica única](../rubrica.md). **Foco específico desta entrega:**

- **N1:** dominar **maturidade MLOps** (níveis 0/1/2), o que vai em `param/metric/artifact` no MLflow, e o ciclo **Stage promotion + Rollback**.
- **N2:** **2.1 (documentação do pipeline)** é a peça que vai para o projeto integrado final. **2.2 (5ª tool na Function)** fecha o ciclo iniciado na Aula 3 — Managed Identity no Online Endpoint + fallback gracioso. **2.3 (drift monitoring)** mostra maturidade operacional.
- **N3 (bônus):** **3.3 (MLOps vs LLMOps)** é particularmente valorizado — é a ponte conceitual desta disciplina com o resto do MBA. Vale entender mesmo se não codar.
- **Reflexão:** discutir **onde a QC está hoje** (provavelmente nível 0) e **onde estará em 12 meses** com o pipeline construído nas Aulas 1-5.

---

## Rotação esperada

Esta é a **última oportunidade de rodízio** antes da entrega final. Quem fez N1 nas Aulas 1-4 deve, idealmente, assumir N2 ou N3 nesta entrega (Critério 4 — Distribuição do trabalho).

---

## Já comece a consolidar para a Aula 6

A Aula 6 é dedicada ao **projeto integrado final** (50% da nota, ZIP no Portal FIAP **1 semana após a aula**, sem apresentação oral). O que adiantar agora:

1. **Diagrama final** da arquitetura QC com **todas as camadas** (Aulas 1-5)
2. **Terraform consolidado** que provisiona TODA a arquitetura da QC
3. **5 tools do agente** documentadas: `/produtos`, `/transcrever`, `/analisar-reviews`, `/analisar-imagem`, `/recomendar`
4. **Esboço da análise FinOps** — calculadora Azure com todos os componentes

Detalhes da entrega final em [../projeto-final/INSTRUCOES.md](../projeto-final/INSTRUCOES.md).
