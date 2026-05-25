# Aula 5 — MLOps na Nuvem

## Objetivos de aprendizagem

Ao final desta aula, você será capaz de:

- Provisionar um **Azure ML Workspace** + **Compute Cluster** com **scale-to-zero** via Terraform.
- Treinar um modelo simples rastreando o experimento com **MLflow** (params, metrics, artifacts).
- Versionar o modelo no **Model Registry** do Azure ML.
- Submeter um **Job reproduzível** no Compute Cluster com **environment** e **data asset** versionados.
- Publicar o modelo como **Managed Online Endpoint** (REST) e consumi-lo.
- Identificar o **nível de maturidade MLOps** (0/1/2) e que automatizações faltam para subir de nível.

> **Importante (perfil dos alunos):** esta disciplina é uma das primeiras do MBA. **Você não precisa saber ML/Python avançado** para fazer os exercícios. O modelo de recomendação é apenas um **veículo didático** para o ciclo MLOps. Modelagem em profundidade é tema da disciplina **AI Foundation and Learning Models**.

---

## Por que esta aula importa para um AI Engineer

Sem MLOps, modelos viram **artefatos em notebooks** que ninguém consegue retreinar, versionar ou auditar. As mesmas ferramentas (Tracking, Registry, Endpoints, Drift Monitoring) seguem relevantes para **LLMOps** — com adaptações (prompt registry, eval framework, RAG quality).

---

## Conexão com o Quantum Commerce

Esta aula entrega o **5º recurso** consumido pelos agentes da QC: um **recomendador de produtos** treinado a partir do catálogo da Aula 2. O modelo é publicado como Endpoint REST e poderia ganhar uma rota `/recomendar` na Function da Aula 3 (exercício N2.2).

---

## Material da aula

| Arquivo | Quando usar |
|---------|-------------|
| [lab/guia-lab.md](lab/guia-lab.md) | Durante a aula — 4 atividades + wrap-up com destroy crítico |
| [lab/terraform/](lab/terraform/) | Workspace + Compute Cluster (scale-to-zero) |
| [lab/notebooks/](lab/notebooks/) | Script local de treino com MLflow tracking + Registry — L₂ |
| [lab/job/](lab/job/) | Job reproduzível (train.py + conda.yml + data-asset.yml + job.yml) — L₃ |
| [lab/endpoint/](lab/endpoint/) | Endpoint + deployment + payload de teste — L₄ |
| [exercicios.md](exercicios.md) | Após a aula — 3 níveis (N1/N2 conceituais; N3 avançado para perfil ML) |

## Entrega de grupo

Esta aula gera a **5ª e última entrega intermediária** (10% da nota): instruções em [entregas/entrega-05/](../../entregas/entrega-05/). Rubrica em [entregas/rubrica.md](../../entregas/rubrica.md).

A Aula 6 é dedicada ao **trabalho em grupo no projeto integrado final** (FinOps + entrega ZIP **1 semana após a Aula 6**, valendo 50%, **sem apresentação oral**) — ver [entregas/projeto-final/](../../entregas/projeto-final/).

---

## ⚠️ Alerta de custo

O **Managed Online Endpoint** custa **~$0,30/h** (Standard_DS3_v2). **Deletar ANTES do `terraform destroy`** — esquecer significa ~$7/dia consumindo seu crédito do Azure for Students.

O Compute Cluster, em contraste, tem **scale-to-zero** (0 nodes idle = custo zero). Sobe automaticamente quando submete um job.

---

## Pré-requisitos

- ✅ Aulas 1-4 concluídas
- ✅ `produtos.csv` da Aula 2 acessível (já está commitado em [`aulas/02-storage-bancos/lab/data/produtos.csv`](../02-storage-bancos/lab/data/produtos.csv) — **não precisa ter a Aula 2 viva**)

> **Sem dependência de Aula 4:** esta aula é independente do AI Services. Se você destruiu a Aula 4, segue normal.
