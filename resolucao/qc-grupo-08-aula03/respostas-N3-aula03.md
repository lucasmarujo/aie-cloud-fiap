# Entrega Aula 03 — Grupo 08 — Nível 3 (N3)

**Disciplina:** Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents
**Turma:** 1AIER
**Data de entrega:** 28/06/2026

> Este documento cobre **exclusivamente a seção 🔴 Nível 3 - N3 (bônus) - Exercícios 3.1 (spec de tool), 3.2 (benchmark), 3.3 (CI/CD + OIDC)** da Entrega 3

## Grupo

| # | Nome completo | GitHub | E-mail FIAP |
|---|---------------|--------|-------------|
| 1 | Tatiana Mastrogiovanni Haddad | https://github.com/TatiHaddad | rm373809@fiap.com.br |
| 2 | Luciana Chaves D'Olivo | https://github.com/l-cdolivo | rm371277@fiap.com.br |
| 3 | Lucas Marujo Amadeu | https://github.com/lucasmarujo | rm370469@fiap.com.br |

## Distribuição do trabalho

| Membro | Nível assumido | Item específico |
|--------|----------------|-----------------|
| **Lucas Marujo Amadeu** | 🟢 **N1 + coordenação** | Exercícios 1.1, 1.2, 1.3, 1.4; montagem do `entrega-grupo-aula03.md` e ZIP |
| **Luciana Chaves D'Olivo** | 🟡 **N2 (completo)** | **Exercícios 2.1 (tool de frete), 2.2 (App Insights), 2.3 (Container Apps) — este documento** |
| **Tatiana Mastrogiovanni Haddad** | 🔴 **N3 (bônus)** | Exercícios 3.1 (spec de tool), 3.2 (benchmark), 3.3 (CI/CD + OIDC) |

> **Rodízio (Critério 4):** na Aula 1 o Lucas fez N2 + N3; na Aula 2 rotacionou
> para N1 + parte do N2 (2.2 — migração). Cumprindo a regra "quem fez N1 nas
> Aulas 1-2 assume N2 ou N3 agora", nesta aula ele assume o **N2 completo**.
> A Tatiana, que vinha de N2/coordenação, rotaciona para N3; a Luciana rotacionou para N1.

---

## 🔴 Nível 3: Tool de Agente + Benchmark + CI/CD — Respostas + Implementação

*Responsável: Tatiana Mastrogiovanni Haddad — Exercícios 3.1 (spec de tool), 3.2 (benchmark), 3.3 (CI/CD + OIDC).*


### Exercício 3.1 — Function como Tool de um Agente AI (conceitual + código)


#### a) Escreva a descrição completa da tool no formato OpenAI Function Calling / Anthropic Tool 


Versão OpenAI Function Calling

```
{
  "type": "function",
  "function": {
    "name": "buscar_produtos_qc",
    "description": "Busca produtos no catálogo da Quantum Commerce com base em categoria e/ou nome. Use quando o usuário perguntar sobre disponibilidade, preço ou características de produtos. NÃO use para status de pedidos, frete, políticas da loja ou assuntos não relacionados ao catálogo.",
    "parameters": {
      "type": "object",
      "properties": {
        "categoria": {
          "type": "string",
          "description": "Categoria do produto. Exemplos: 'moveis', 'eletronicos', 'informatica', 'cozinha', 'esportes'."
        },
        "nome": {
          "type": "string",
          "description": "Nome ou parte do nome do produto. Ex: 'cadeira ergonomica', 'Samsung S24'."
        }
      },
      "required": []
    }
  }
}
```



Versão Antropic Tool

```
{
  "name": "buscar_produtos_qc",
  "description": "Busca produtos no catálogo da Quantum Commerce com base em categoria e/ou nome. Use esta tool quando o usuário perguntar sobre disponibilidade, preço, características ou existência de um produto específico ou categoria de produtos. NÃO use esta tool para perguntas sobre políticas da loja, status de pedidos, frete ou assuntos não relacionados ao catálogo. Prefira categorias amplas quando o usuário for vago ('eletrônicos', 'móveis', 'cozinha'). Se o usuário mencionar uma marca ou modelo específico, passe no campo 'nome'. Ambos os parâmetros são opcionais — você pode buscar só por categoria, só por nome, ou pelos dois.",
  "input_schema": {
    "type": "object",
    "properties": {
      "categoria": {
        "type": "string", 
        "description": "Categoria do produto no catálogo da QC. Exemplos válidos: 'moveis', 'eletronicos', 'informatica', 'cozinha', 'esportes', 'moda'. Use apenas uma categoria por chamada. Deixe vazio se o usuário não especificou categoria."
        },
      "nome": {
        "type": "string", 
        "description": "Nome ou parte do nome do produto. Exemplos: 'cadeira ergonomica', 'Samsung S24', 'cafeteira nespresso'. Pode ser um termo parcial — a busca é por substring. Deixe vazio se o usuário não mencionou um produto específico."
        }
    },
    "required": []
  }
}
```



#### b) Escreva 3 exemplos de conversas usuário-agente onde o agente decide chamar a tool:

1) "Tem cadeira boa para home office?"
2) "Quanto custa o Samsung S24?"
3) "Preciso de algo para café"


1) "Tem cadeira boa para home office?"

Usuário: Tem cadeira boa para home office?

[Agente analisa: usuário quer produto → deve chamar a tool]
[Tool call: buscar_produtos_qc(categoria="moveis", nome="cadeira")]


Tool response:
[
  {"id": 1, "nome": "Cadeira Ergonômica DXRacer", "preco": 1299.90, "categoria": "moveis"},
  {"id": 7, "nome": "Cadeira de Escritório Mesh Pro", "preco": 899.00, "categoria": "moveis"},
  {"id": 12, "nome": "Cadeira Gamer ThunderX3", "preco": 1599.00, "categoria": "moveis"}
]


Agente: Temos ótimas opções para home office! A mais popular é a Cadeira Ergonômica DXRacer por R$ 1.299,90, com suporte lombar e ajuste de altura. Se preferir algo mais em conta, a Cadeira Mesh Pro custa R$ 899,00 e tem excelente ventilação. Quer saber mais detalhes de alguma delas ou ver outras opções?



2) "Quanto custa o Samsung S24?"

Usuário: Quanto custa o Samsung S24?

[Agente analisa: usuário quer preço de produto específico → deve chamar a tool]
[Tool call: buscar_produtos_qc(categoria="eletronicos", nome="Samsung S24")]

Tool response:
[
  {"id": 5, "nome": "Smartphone Samsung Galaxy S24", "preco": 3999.00, "categoria": "eletronicos"},
  {"id": 6, "nome": "Smartphone Samsung Galaxy S24+", "preco": 4799.00, "categoria": "eletronicos"}
]

Agente: O Samsung Galaxy S24 está disponível por R$ 3.999,00. Também temos o modelo S24+ por R$ 4. 99,00, com tela maior e mais armazenamento. Deseja adicionar algum ao carrinho ou quer comparar as especificações?



3) "Preciso de algo para café"

Usuário: Preciso de algo para café

[Agente analisa: usuário vago, mas claramente sobre produto → deve chamar a tool]
[Tool call: buscar_produtos_qc(categoria="cozinha", nome="cafe")]

Tool response:
[
  {"id": 3, "nome": "Cafeteira Nespresso Essenza Mini", "preco": 399.00, "categoria": "cozinha"},
  {"id": 8, "nome": "Moedor de Café Elétrico 150W", "preco": 189.00, "categoria": "cozinha"},
  {"id": 15, "nome": "Prensa Francesa 600ml", "preco": 89.90, "categoria": "cozinha"}
]

Agente: Tenho algumas opções para o seu café! Para praticidade, a Cafeteira Nespresso Essenza Mini por R$ 399,00 é a mais popular. Se preferir moer seu próprio grão, temos o Moedor Elétrico 150W por R$ 189,00. Ou, para um café mais artesanal, a Prensa Francesa por R$ 89,90. Qual estilo de preparo você prefere?


#### c) Identifique 2 casos onde o agente NÃO deve chamar a tool mesmo o usuário falando de produto. Justifique.


Caso 1: Pergunta sobre status de pedido
Usuário: "Meu pedido do Samsung S24 chegou quando?"

Apesar de mencionar um produto específico do catálogo, Samsung S24, a pergunta é sobre o status de entrega de um pedido específico do usuário e não sobre o catálogo. A tool buscar_produtos_qc retornaria dados de catálogo como preço e categoria, que são irrelevantes para a pergunta.
O agente deve encaminhar para a tool de rastreamento de pedido ou informar que não tem acesso ao dado espeífico.


Caso 2: Pergunta sobre política da loja
Usuário: "Vocês têm frete grátis para produtos de eletrônicos?"

A pergunta usa o termo eletrônicos que é uma categoria do catálogo, mas o que o usuário quer saber é sobre a política de frete da QC e não sobre produtos específicos.
Chamar buscar_produtos_qc passando parâmetro da categoria eletrônicos retornaria uma lista de produtos e não a informação sobre o frete, sendo uma resposta irrelevante e confusa.
O agente deve responder com base no conhecimento sobre políticas da loja ou chamar  tool calcular_frete.


#### d) Reflexão: Como você manteria a descrição da tool sincronizada com mudanças no endpoint? (Versionamento, contract testing, OpenAPI spec)

Levando em consideração que o maior risco é o drift entre a tool spec e a API real, já que se o endpoint muda, por receber novos parâmetros, ter alguma categoria renomeada ou pela mudança de comportamento, e a descrição da tool não é atualizada , o agente vai realizar as chamadas passando parâmetros errados.

Com esse ponto, utilizando a OpenAPI Spec, a function expõe um openai.json "/api/openai.json", que descreve todos os endpoints, parâmetros e tipos. A descrição da tool é gerada automaticamente através do spec e não gerada manualmente. Com isso, qualquer alteração na API atualiza o spec que por sua vez atualiza a tool.


Com o contract testing no CI/CD, no pipeline é incluído um step para validar se a tool spec atual ainda é compatível com a API real, se o endpoint mudar de forma incompatível o pipeline falha antes do deploy.


Usando o versionamento da tool, com versão explícita como por exemplo, buscar_produtos_qc_v2.
Dessa forma, o agente continua usando a versão anterior até ser explicitamente migrado e com isso evita quebrar o agente em produção com mudanças de backend.


E realizando teste de integração agente-tool: incluindo no pipeline um teste que instancia o agente com a tool spec atual e envia perguntas para verificar se os parâmetros gerados ainda são válidos para a API.


#### Exercício 3.2 — Benchmark de carga


Resultados: Azure Function
FUNC_URL="https://func-qc-9xjp7v.azurewebsites.net/api/produtos?categoria=moveis"
ACI_URL="http://<ip-aci>:8080/produtos?categoria=moveis"

hey -n 1000 -c 50 "$FUNC_HOST/api/produtos?categoria=moveis"


Summary:
  Total:        3.7536 secs
  Slowest:      2.8761 secs
  Fastest:      0.0361 secs
  Average:      0.1525 secs
  Requests/sec: 266.4114

Latency distribution:
  50% in 0.0429 secs
  75% in 0.0464 secs
  90% in 0.0516 secs
  95% in 2.0227 secs
  99% in 2.3398 secs

Status code distribution:
  [200] 1000 responses


Resultados: ACI
hey -n 1000 -c 50 "http://$ACI_FQDN:8080/produtos?categoria=moveis"

Summary:
  Total:        7.7728 secs
  Slowest:      1.4529 secs
  Fastest:      0.0331 secs
  Average:      0.3689 secs
  Requests/sec: 128.6532

Latency distribution:
  50% in 0.3498 secs
  75% in 0.4337 secs
  90% in 0.5456 secs
  95% in 0.6321 secs
  99% in 1.1442 secs

Status code distribution:
  [200] 1000 responses


  | Métrica | Function | ACI |
|---------|----------|-----|
| Latência média | 152 ms | 369 ms |
| p95 | 2.022 ms | 632 ms |
| Throughput | 266,4 req/s | 128,6 req/s |
| Erros | 0% | 0% |
| Custo aprox por 1M req | ~0,81 | ~35,77 por mês (fixo) |


#### Reflexão
a) Qual aguentou melhor a carga? Por quê? 
O ACI venceu disparado com relação a latência, 6x menor, e throughput, 4,6x maior.
Isso ocorre poruqe o container do FastAPI no ACI está sempre quente com as conexões já pré-estabelecidas com os processos pythons já inicializados. E enquanto isso, a Function Flex Consumption precisa instanciar o worker Python a cada cold start, adicionando o tempo de 2 segundos nos primeiros requests de cada instância.


b) Em qual cenário a Function venceria? Em qual o ACI venceria? 
Function: venceria em workloads esporádicos ou com tráfego muito variável, tendo custo quase zero sem tráfego.

ACI: venceria em workloads previsíveis e de baixa latência, onde a API de busca de produtos é chamada constantemente pelos agentes. E o custo fixo do ACI se justifica quando o tráfego é alto e constante.


c) Como você arquitetaria a API da QC para suportar Black Friday (10x tráfego)?
Usando camada de criticidade de forma híbrida.

Busca de produtos com latência crítica, container apps usa a combinação do custo zero servless e a previsibilidade de latência do container.

Cálculo de Frete como esporádico, Function já que 50k de chamadas ao mês não justifica ter o container sempre ativo.

Buffer de pico, já que na blackfriday mais de 80% das buscas se referem aos mesmos produtos em oferta. O cache absorve o pico sem necessitar escalar o backend de forma linear.

Circuit breaker, se o backend saturar, retorna o resultado do cache com TTL estendido ao inves de retornar o erro 500.


#### Exercício 3.3 — Pipeline CI/CD para a Function
Arquivo: .github/workflows/deploy-function.yml
Arquivo de teste: aula03/function/tests/test_function.py


Como configurar o OIDC no Azure

O OIDC elimina a necessidade de armazenar AZURE_CLIENT_SECRET no GitHub. O GitHub Actions se autentica diretamente via token federado.

```
# 1. Criar App Registration (Service Principal) para o CI/CD
az ad app create --display-name "github-actions-qc"

# 2. Capturar o client-id
APP_ID=$(az ad app list --display-name "github-actions-qc" --query "[0].appId" -o tsv)

# 3. Criar credencial federada (vincula o repo GitHub ao App Registration)
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:lucasmarujo/aie-cloud-fiap:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# 4. Criar Service Principal e dar permissão de Contributor no Resource Group
az ad sp create --id $APP_ID
az role assignment create \
  --assignee $APP_ID \
  --role "Contributor" \
  --scope "/subscriptions/<SUB_ID>/resourceGroups/rg-qc-aula03-<SUFIXO>"

# 5. Adicionar secrets no GitHub (sem senha — só IDs)
# AZURE_CLIENT_ID = $APP_ID
# AZURE_TENANT_ID = $(az account show --query tenantId -o tsv)
# AZURE_SUBSCRIPTION_ID = $(az account show --query id -o tsv)
# SUFIXO = 9xjp7v (sufixo aleatório do Terraform)
```


Com o uso do OIDC não se faz necessáiro incluir senhas mitigando o problema de risco de vazamento de credencial no Git. O uso de Token deixa a vida curta do processo e o escopo limitado ao job em execução. Torna o processo auditável, cada execução do pipeline tem log do Azure e não se faz necessário a rotação manual dos secrets já que os tokens são gerados de forma automática.
