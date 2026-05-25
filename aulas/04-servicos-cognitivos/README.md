# Aula 4 — Serviços Cognitivos & APIs

## Objetivos de aprendizagem

Ao final desta aula, você será capaz de:

- Consumir APIs cognitivas prontas da Azure: **Speech-to-Text** (PT-BR), **Language** (sentimento + entidades) e **Vision** (tags + OCR + caption).
- Provisionar um **Azure AI Services multi-service** (1 endpoint para Speech/Language/Vision) com **custom subdomain** habilitado.
- Autenticar a Function nas APIs cognitivas via **Managed Identity** (sem chaves no código).
- Decidir entre **APIs prontas**, **modelos customizados** (Custom Vision, CLU) e **LLMs** (Azure OpenAI) para cada caso de uso.
- Construir um **pipeline cognitivo end-to-end**: Function lê áudio/imagem do Blob, transcreve/analisa, grava de volta no Cosmos.

---

## Por que esta aula importa para um AI Engineer

Os agentes da QC precisam **ouvir**, **ler** e **ver** — não só processar texto. As **APIs cognitivas prontas** dão essas capacidades em minutos, sem treinar nada. A escolha entre pronta/custom/LLM define **custo, latência e qualidade** da experiência conversacional.

---

## Conexão com o Quantum Commerce

Esta aula adiciona **3 novas tools** à API da QC (sobre a Function da Aula 3):

| Tool | Capacidade cognitiva |
|------|----------------------|
| `/transcrever` | Speech-to-Text — transcrever atendimento de voz |
| `/analisar-reviews` | Language — sentimento + entidades das reviews do Cosmos |
| `/analisar-imagem` | Vision — tags + OCR + caption das imagens dos produtos |

Os agentes da QC podem agora **ouvir** o cliente, **entender** as reviews e **ver** as imagens dos produtos.

---

## Material da aula

| Arquivo | Quando usar |
|---------|-------------|
| [lab/guia-lab.md](lab/guia-lab.md) | Durante a aula — 4 atividades intercaladas |
| [lab/terraform/](lab/terraform/) | Código IaC: AI Services + Key Vault + Function + roles |
| [lab/function/](lab/function/) | Function consolidada (`/health`, `/transcrever`, `/analisar-reviews`, `/analisar-imagem`) |
| [lab/scripts/](lab/scripts/) | Script opcional de TTS para gerar áudio de teste |
| [exercicios.md](exercicios.md) | Após a aula — exercícios em 3 níveis (N3 inclui Azure OpenAI + embeddings reais) |

## Entrega de grupo

Esta aula gera a **4ª entrega de grupo** (10% da nota): instruções em [entregas/entrega-04/](../../entregas/entrega-04/). Rubrica em [entregas/rubrica.md](../../entregas/rubrica.md).

---

## Pré-requisitos

- ✅ Aulas 1-3 concluídas
- ✅ **Storage e Cosmos da Aula 2 aplicados** (com `produtos.csv` no Blob e reviews populadas no Cosmos)

Se você destruiu a Aula 2:

```bash
cd ~/aie-cloud/aulas/02-storage-bancos/lab/terraform
SQL_PASSWORD=$(openssl rand -base64 24)
terraform apply -auto-approve -var="sql_admin_password=$SQL_PASSWORD"
# Re-popular o Cosmos com reviews (ver guia da Aula 2, Atividade 3)
```
