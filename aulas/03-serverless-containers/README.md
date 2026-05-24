# Aula 3 — Compute Avançado: Serverless, VMs e Containers

## Objetivos de aprendizagem

Ao final desta aula, você será capaz de:

- Comparar os três modelos de compute: VMs, Containers e Serverless (Functions).
- Decidir qual modelo usar para cada tipo de workload.
- Empacotar uma aplicação Python em container e rodar no Azure Container Instances (ACI).
- Implantar uma Azure Function (HTTP trigger) e entender o modelo de cobrança serverless.
- Entender o papel do Kubernetes (AKS) e quando ele NÃO é a melhor escolha.
- Aplicar segurança: Managed Identity em Functions, secrets via KeyVault.

---

## Conexão com o Quantum Commerce

Você implanta **microserviços/funções** que servem o backend da Quantum Commerce: API de catálogo (Function HTTP), worker de processamento de pedidos (Function com trigger de Queue), e um container com a aplicação web.

---

## Ambiente complementar

A partir desta aula introduzimos o **GitHub Codespaces** (60h/mês gratuitas) para quando precisarmos de Docker localmente para testes antes de subir para a nuvem.

---

## Material da aula

> Em construção — disponível antes da aula.

- `lab/` — Deploy de Function + Container no Azure
- `exercicios/` — Migrar uma aplicação monolítica para serverless

---

## Pré-requisitos

- Aulas 1 e 2 concluídas (storage e banco da Quantum Commerce provisionados)
