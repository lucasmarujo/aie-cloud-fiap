# Arquitetura QC — Aula 4 (camada cognitiva)

Evolução da arquitetura da Quantum Commerce com a **camada cognitiva** adicionada
sobre a base das Aulas 2 (Storage/Cosmos/AI Search) e 3 (Function como tools do agente).
Toda comunicação com serviços cognitivos usa **Managed Identity** (sem chave em código).

```mermaid
flowchart TB
    subgraph Clientes
        U["Cliente / App / Telefonia"]
    end

    subgraph Function["Azure Function — tools do agente (MI SystemAssigned)"]
        H["/health"]
        T["/transcrever — STT"]
        AR["/analisar-reviews — pipeline 2.1"]
        AI_IMG["/analisar-imagem — Vision"]
        SUM["/sumarizar-reviews-produto — LLM 3.3"]
    end

    subgraph Cognitivo["Camada Cognitiva (AI Services + Azure OpenAI)"]
        SP["Speech<br/>STT batch/real-time · TTS Neural"]
        LG["Language<br/>PII redaction · sentimento · opinion mining · entidades · summarization"]
        VI["Vision<br/>Tags · OCR/Read · Caption · Object Detection"]
        OAI["Azure OpenAI<br/>text-embedding-3-small (3.1)<br/>gpt-4o-mini (3.3)"]
    end

    subgraph Dados["Dados (Aula 2)"]
        BLOB["Blob Storage<br/>gravacoes · imagens · catalogo"]
        COS[("Cosmos DB<br/>qc-db / reviews")]
        SRCH["AI Search<br/>produtos-index + content_vector 1536"]
    end

    U --> Function

    T --> BLOB
    T -->|token AAD MI| SP
    T -->|transcrito redigido| LG

    AR -->|1. PII → 2. sentimento/aspectos<br/>3. entidades → 4. resumo| LG
    AR -->|upsert schema completo| COS

    AI_IMG --> BLOB
    AI_IMG -->|token AAD MI| VI

    SUM -->|lê reviews enriquecidas| COS
    SUM -->|prompt estruturado → JSON| OAI

    OAI -.->|embeddings do catálogo| SRCH
    BLOB -.->|produtos.csv| OAI

    classDef cog fill:#e8f0fe,stroke:#4285f4,color:#111;
    classDef data fill:#e6f4ea,stroke:#34a853,color:#111;
    classDef fn fill:#fef7e0,stroke:#f9ab00,color:#111;
    class SP,LG,VI,OAI cog;
    class BLOB,COS,SRCH data;
    class H,T,AR,AI_IMG,SUM fn;
```

## Legenda dos fluxos

| Fluxo | Rota | Serviço cognitivo | Persistência |
|-------|------|-------------------|--------------|
| Voz → texto → análise pós-call (2.2) | `/transcrever` | Speech STT → Language | Cosmos |
| Pipeline robusto de reviews (2.1) | `/analisar-reviews` | Language (PII → opinion mining → entidades → resumo) | Cosmos `reviews` |
| Análise de imagem de produto (1.4/2.3) | `/analisar-imagem` | Vision | — |
| Vector search real (3.1) | script `gerar_embeddings_vector.py` | Azure OpenAI `text-embedding-3-small` | AI Search `content_vector` |
| Síntese por produto (3.3) | `/sumarizar-reviews-produto` | Azure OpenAI `gpt-4o-mini` | lê Cosmos `reviews` |

## Segurança (Ex. 1.3)

Todas as setas para a camada cognitiva usam **token AAD via Managed Identity**, não API key.
Pré-requisitos: `custom_subdomain_name` nos `azurerm_cognitive_account` + roles
`Cognitive Services User` (Language/Vision) e `Cognitive Services OpenAI User` (OpenAI)
atribuídas à MI da Function.
