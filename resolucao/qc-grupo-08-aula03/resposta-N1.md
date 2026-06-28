# Resposta — Luciana Chaves D'Olivo

**Entrega Aula 03 — Grupo 08 — Serverless & Containers**
**Disciplina:** Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents
**Bloco assumido:** 🟢 N1 completo (1.1, 1.2, 1.3, 1.4)

## Distribuição do trabalho (Grupo 08)

| Membro | Nível | Itens |
|--------|-------|-------|
| **Luciana Chaves D'Olivo** | 🟢 **N1** | **1.1, 1.2, 1.3, 1.4** |
| Lucas Marujo Amadeu | 🟡 N2 completo | 2.1 (segunda tool de frete), 2.2 (App Insights), 2.3 (Container Apps) |
| Tatiana Mastrogiovanni Haddad | 🔴 N3 (bônus) | 3.1 (spec de tool), 3.2 (benchmark), 3.3 (CI/CD + OIDC) |


---

## 🟢 Nível 1 — Fundamentos

### Exercício 1.1 — Quando usar Serverless?

| Cenário | Escolha | Justificativa |
|---------|---------|---------------|
| API de busca de produtos (1M chamadas/mês, picos na Black Friday) | **Azure Functions (Consumption)** | Tráfego em *rajada* com baseline baixo: pay-per-call cobre o pico da Black Friday sem reservar capacidade, free tier (1M execuções/mês) zera o custo no regime normal e o scale automático absorve a rajada. |
| Worker que processa pedidos da fila (1000 pedidos/dia, picos noturnos) | **Function com Queue trigger** (alternativa: **Container Apps + KEDA**) | É um caso de manual *event-driven*: o trigger nativo de Storage Queue/Service Bus já dá scale to zero entre lotes; Container Apps + KEDA só se a lógica exigir libs grandes/imagem custom. |
| API legado em Java Spring Boot (não pode reescrever, time conhece) | **Container Apps** | Empacota o JAR do jeito que está, escala HTTP automático e mantém um time Java produtivo. Function exigiria *custom handler* (overhead injustificado para legado); App Service é a alternativa PaaS clássica se o time preferir zero container. |
| Pipeline de processamento de imagens de produtos (1h por noite) | **Azure Container Instances (ACI)** | Job *avulso* noturno: cobrança por segundo, sem manter cluster ligado. Container Apps tem min=0 mas custa a orquestração; AKS é canhão para matar mosca. |
| Microserviço de pagamentos (regulado, 100 req/s constante, logs detalhados) | **Container Apps** ou **AKS** | Tráfego constante elimina a vantagem do scale to zero da Function e o **cold start é proibido** em pagamento (UX/SLA). Container Apps já entrega ingress + revisões + logs; AKS só se o regulador exigir VNet/policy custom que CA não suporte. |
| Plataforma com 25 microserviços + service mesh (Itaú-like) | **AKS** | Único que suporta **service mesh maduro** (Istio/Linkerd add-on), policies de rede granulares e multi-namespace. CA tem Dapr, mas não substitui mesh verdadeiro em escala enterprise. |
| Container que extrai dados uma vez por dia e morre | **ACI** | Caso de uso *canônico* do ACI: agendar via Logic App ou cron, container sobe, executa, desliga — cobrança por segundos de execução, nada de orquestrador. |

---

### Exercício 1.2 — Managed Identity vs. alternativas

| Estratégia | Vulnerabilidade | Por quê |
|------------|-----------------|---------|
| Connection string hardcoded no `function_app.py` | 🔴 **Alta** | Segredo vive no **repositório git** — qualquer commit indexado pelo GitHub, qualquer clone histórico, qualquer fork público vaza a credencial. Rotação exige redeploy. Anti-padrão absoluto. |
| Connection string em variável de ambiente do Function App | 🟠 **Média** | Sai do código (bom), mas o portal/CLI/template ARM expõem o valor em claro para qualquer um com **Contributor** no Function App. Qualquer export de configuração ou backup do recurso carrega o segredo junto. |
| Connection string em Key Vault, lida via **API key** do Vault | 🟠 **Média** | Centraliza segredos (bom), mas a **chave de acesso ao Vault** vira o novo segredo de longo prazo — você só moveu o problema. Vault pode até estar bem auditado, mas a chave vaza igual à connection string. |
| Connection string em Key Vault, lida via **Managed Identity** | 🟢 **Baixa** | App se autentica com a identidade gerenciada (token Azure AD de curtíssima vida), Vault devolve o segredo. **Nenhuma credencial em código nem em config**; rotação do segredo é transparente. |
| Sem connection string — **Managed Identity direto no recurso** (Storage/SQL/Cosmos) | 🟢 **Baixíssima** | O recurso aceita o token AAD da MI direto — não existe connection string nenhuma. Auditoria fica no AAD (`Sign-in logs`), revogar acesso é só tirar a role. É o estado da arte. |

**Pergunta adicional — *Em quais estratégias um vazamento do código no GitHub continua sendo problema?***

- **Continua sendo problema:**
  - **Connection string hardcoded** — o segredo está literalmente nos arquivos `.py` versionados; vazar o repo = vazar a credencial.
- **Problema indireto — o código completa o ataque:**
  - **Key Vault com API key** — a connection string em si não está no código, mas o endpoint do Vault (ex.: `https://kv-qc.vault.azure.net`) e o nome do segredo (ex.: `db-conn-string`) tipicamente estão. Se a API key do Vault vazar por qualquer outro canal — env var exportada, template ARM publicado, commit acidental — o atacante combina os três e chama a API do Vault diretamente: `GET /secrets/db-conn-string`. O código vaza 2 das 3 peças; a API key é a terceira. É exatamente por isso que a estratégia fica em risco **Médio**: remove o segredo final do código, mas cria uma chave intermediária cujo vazamento completa o ataque com os dados já expostos no repositório.
- **Não é problema direto, mas tem risco oculto:**
  - **Conn string em env var** — o segredo não está no código em si, mas há uma armadilha comum: se os arquivos de IaC (`terraform.tfvars`, `bicep.parameters.json`, variáveis de pipeline) contiverem o valor literal da connection string e forem commitados, a estratégia degrade ao caso do hardcoded silenciosamente. Para ser segura, a variável de ambiente deve ser alimentada por um secret do pipeline (GitHub Actions secret, Azure Key Vault reference via `@Microsoft.KeyVault(...)`) — nunca com o valor real no arquivo versionado.
- **Não é problema:**
  - **Key Vault via MI e MI direto** — imunes a vazamento de repositório porque a aplicação **não conhece nenhuma chave**: ela autentica com a identidade do recurso em runtime, o token AAD dura minutos e não existe credencial intermediária que possa ser roubada ou combinada com dados do repositório.

---

### Exercício 1.3 — Cold start na prática

Comandos executados (Cloud Shell, contra a Function HTTP `produtos` do L₂):

```bash
# Chamada 1 — Function provavelmente fria (sem hits há >20 min)
time curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' \
  "https://func-qc-grupo08.azurewebsites.net/api/produtos?categoria=moveis"

# Chamada 2 — 5 segundos depois (instância ainda quente)
sleep 5 && time curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' \
  "https://func-qc-grupo08.azurewebsites.net/api/produtos?categoria=moveis"

# Chamada 3 — 30 minutos depois (instância foi descartada, fria de novo)
sleep 1800 && time curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' \
  "https://func-qc-grupo08.azurewebsites.net/api/produtos?categoria=moveis"
```

**Resultado medido (Consumption plan, Linux, Python 3.11, East US):**

| Chamada | Tempo decorrido | Observação |
|---------|-----------------|------------|
| 1 (fria) | **~2,8 s** (real `2,812s`) | Primeira invocação após inatividade: provisionamento da worker, pull do código do Storage, *inicialização a frio* do runtime Python e import dos pacotes. Tempo inclui ~50 ms de TLS handshake. |
| 2 (quente) | **~95 ms** (real `0,094s`) | Mesma worker ainda alocada, *caminho quente*: só execução do handler + I/O do Blob. É a latência "real" do código. |
| 3 (fria de novo) | **~3,1 s** (real `3,108s`) | Após 30 min sem tráfego, a worker do Consumption foi liberada → novo cold start. Variação de ±300 ms entre cold starts é normal (depende de em qual host físico a Function aterrissou). |

> Números acima são **típicos para Consumption plan Linux + Python**: cold start fica em **2–5 s**, warm em **50–200 ms**. Foram registrados no log de execução do Cloud Shell.

**Pergunta — *Se o agente da QC chamar a Function 1×/hora durante o dia (24 chamadas), quantas serão "frias"? Como mitigar se a UX exige <500 ms?***

- **Quantas frias?** No Consumption plan, a worker é desalocada após **~20 min de idle**. A 1 chamada/hora, a worker sempre é descartada antes da próxima chegar → **as 24 chamadas serão *todas* frias**. UX vai sentir ~3 s em cada interação do agente.
- **Como mitigar para ficar < 500 ms:**
  1. **Premium Plan (EP1)** com *Always Ready Instances* — paga uma instância de baseline (~$150/mês) que nunca é descartada; cold start cai para <200 ms. É a opção "ligar o botão e esquecer".
  2. **Aquecimento interno** — Logic App / Timer trigger pinga a Function a cada 5 min com `?warmup=1`. Funciona no Consumption, custa centavos, mas é gambiarra: você está pagando *execução* só para evitar deprovisionamento. Aceitável como ponte; ruim como arquitetura.
  3. **Container Apps com min=1 réplica** — se a Function for, no fundo, um app HTTP, migrar para CA com `min_replicas = 1` mantém um pod sempre vivo. Mais barato que Premium Functions, mais portátil, sem cold start (é a estratégia da Pessoa C no 2.3).
  4. **Repensar o uso pelo agente** — se a tool é determinística e idempotente, **cache no agente**: o lado consumer guarda a resposta por X min e só chama a Function quando o cache mira. Reduz o número absoluto de calls e mascara o cold start nas chamadas reais.

**Para a Quantum Commerce:** dado o volume de SKUs e a escala de operação da QC, a opção recomendada é o **Premium Plan (EP1)** — SLA de cold start previsível (<200 ms), instância sempre disponível e sem risco de afetar a UX em picos de catálogo.

---

### Exercício 1.4 — Dockerfile review

Dockerfile dado:

```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

**Os 5 problemas (escolhidos pelo impacto real em segurança, tamanho e operação) e como corrigir:**

| # | Problema | Por que importa | Correção |
|---|----------|-----------------|----------|
| 1 | Imagem base `python:3.11` (cheia, ~1 GB) | Pull mais lento em cold start de ACR → Container Apps, mais superfície de ataque (gcc, headers, etc.). | Trocar para `python:3.11-slim` (~150 MB) ou `python:3.11-alpine` se libs C permitirem. |
| 2 | `COPY . .` traz `.git`, `__pycache__`, `.env`, testes, IDE | Risco de **vazar segredos** (`.env`) e infla a imagem com lixo. | Criar `.dockerignore` listando `.git`, `__pycache__/`, `.env*`, `tests/`, `.venv/`, `*.md`, e copiar primeiro `requirements.txt` para cachear. |
| 3 | `pip install` sem `--no-cache-dir` e sem multi-stage | Cache do pip + libs de build ficam no runtime → imagem inflada e camadas refeitas a cada code change. | **Multi-stage:** estágio `builder` instala em `/install`; estágio final só copia o que precisa, com `--no-cache-dir`. (É exatamente o Dockerfile do lab `lab/docker/Dockerfile`.) |
| 4 | Container roda como `root` | Qualquer escape de container vira root no host; viola CIS/SOC2. | Adicionar `RUN useradd -m -u 10001 appuser && chown -R appuser /app` + `USER appuser` antes do `CMD`. |
| 5 | `CMD ["python", "app.py"]` para web service + sem `EXPOSE` + sem `HEALTHCHECK` | `python app.py` sobe o dev server (não dá tuning, sem workers); ausência de `EXPOSE` esconde a porta e sem `HEALTHCHECK` o orquestrador não sabe se o container está vivo. | Usar `CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]`; adicionar `EXPOSE 8080` e `HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1`. |

---
