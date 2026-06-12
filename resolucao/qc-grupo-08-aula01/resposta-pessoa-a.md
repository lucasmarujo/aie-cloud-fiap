# Entrega Aula 01 — Grupo 08

**Disciplina:** Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents
**Turma:** 1AIER
**Data de entrega:** <DD/MM/AAAA>

## Grupo

| # | Nome completo                   | GitHub                           | E-mail FIAP          |
|---|---------------------------------|----------------------------------|----------------------|
| 1 | Tatiana Mastrogiovanni Haddad   | https://github.com/TatiHaddad    | rm373809@fiap.com.br |
| 2 | Luciana Chaves D'Olivo          | https://github.com/l-cdolivo     | rm371277@fiap.com.br |
| 3 | Lucas Marujo Amadeu             | https://github.com/lucasmarujo   | rm370469@fiap.com.br |

## Distribuição do trabalho

| Membro                  | Nível assumido          | Item específico                                                                |
|-------------------------|-------------------------|--------------------------------------------------------------------------------|
| Tatiana Mastrogiovanni  | 🟢 N1 + 🔴 N3 (bônus)  | Exercícios 1.1, 1.2, 1.3, 1.4 + 3.3 (multi-cloud)                              |
| Luciana Chaves D'Olivo  | 🟡 N2 + coordenação    | Exercício 2.1 (arquitetura + diagrama) + 2.3; montagem do doc, reflexão e ZIP  |
| Lucas Marujo Amadeu     | 🟡 N2 + 🔴 N3 (bônus)  | Exercício 2.2 (custos) + 3.1 (Terraform) + 3.2 (Bicep)                         |

> Regra: cada membro deve ter pelo menos uma contribuição. O **rodízio entre aulas** (quem fez N1 antes faz N2 depois) é incentivado e vale o ponto do Critério 4 (ver [rubrica.md](rubrica.md)).

---

## 🟢 Nível 1 — Respostas

Exercícios: 1.1, 1.2, 1.3, 1.4 (N1 completo) + 3.3 (N3 bônus — Multi-cloud)

Exercício 1.1 — Mapeamento de modelos de serviço
Para cada serviço, identifique se é IaaS, PaaS, SaaS ou FaaS. Justifique em uma frase.

| Serviço                              | Modelo | Justificativa                                                                                                                            |
|--------------------------------------|--------|------------------------------------------------------------------------------------------------------------------------------------------|
| Gmail                                | SaaS   | Aplicação completa entregue via browser onde o usuário não gerencia nenhuma camada de infraestrutura ou plataforma.                      |
| Azure Virtual Machines               | IaaS   | O usuário provisiona e gerencia o Sistema Operacional, rede e armazenamente. A Microsoft fornece apenas o hardware vistualizado.         |
| Azure App Service (hospedar uma API) | PaaS   | O desenvolvedor faz o deploy do código. E a plataforma cuida do Sistema Operacional, runtime, escalonament e patches.                    |
| AWS Lmbda                            | FaaS   | Execução de funções sob demanda sem necessidade de gerenciar servidor. Cobrnaça realizada por invocações e tempo de execução.            |
| Azure SQL Database                   | PaaS   | Banco de Dados gerenciado, o usuário administra esquemas e os dados e a Microsoft cuida do Sistema Operacional, backup e HA.             |
| Salesforce CRM                       | SaaS   | CRM completo entregue como serviço. Personalização via configuração e não via infraestrutura.                                            |
| Google Kubernetes Engine (GKE)       | PaaS   | O control plane do K8s é grenciado pelo Google. O usuario gerencia os workloads e os nós, com elementos de IaaS no worker nodes.         |
| Azure Blob Storage                   | IaaS   | Armazenamento de objetos de baixo nível gerenciado pelo usuário. Não tem camada de aplicação sobre o dado.                               |
| Azure OpenAI Service                 | PaaS   | API gerenciada de modelos de IA. O usuário consome endpoints sem a necessidade de gerenciar modelos, GPUs ou infraestrutura subjacente.  |



Exercício 1.2 — Os 6 Rs na prática
Leia cada cenário e escolha o R de migração mais adequado (Rehost, Replatform, Refactor, Repurchase, Retire, Retain). Justifique.

Cenário A: 
R escolhido: Rehost (Lift & Shift)
Justificativa: O sistema de rastreamento de frotas possui código legado de 2008 e tem expectativa de migração rápida, como o objetivo é ganhar elasticidade com o menor risco possível.
Sabendo que não possui documentação e que apenas uma pessoa conhece o sistema, qualquer rafatoração eleva o risco significativamente. Com isso, o Rehost move a VM para a nuvem sem necessidade alguma de alteração.
Entregando elasticidade e resiliência com prazo e risco mínimos.


Cenário B: 
R escolhido: Retire
Justificativa: O ERP de RH é local e possui menos de 5 usuários ativos por mês, com isso o uso se mostra insignificante.
Manter uma estrutura de infraestrutura tem custo operacional e também de segurança e esse custo não tem retorno devido a falta de usabilidade.
Levando tudo isso em consideração a ação mais correta é descontinuar o sistema, arquivar os dados conforme a política de retenção e redirecionar os poucos usuários para outra solução.


Cenário C: 
R escolhido: Refactor (Re-architect)
Justificativa: Considerando que a Fintech já decidiu aproveitar a migração para reestruturar a aplicação em microserviços com K8s e event-driven.
A API de pagamento é monolítica e a refatoração está planejada para microserviços, exigindo reescrita parcial da arquittura e caracterizando uma refatoração.
Com isso, o ganho é de escalabilidade independente por serviço e maior resiliência a falhas.


Cenário D: 
R escolhido: Repurhase
Justificativa: Considerando que o SaaS de mercado vai atender quase a totalidade das necessidades por custo menor, substituir o sistema proprietário é a decisão economicamente racional.
Eliminando dívida técnica e liberando o time para atividades de maior valor.


Cenário E: 
R escolhido: Retain (Revisit)
Justificativa: Mainframe com dados de cliente e que por decisão do Banco Central os dados do cliente devem ficar on-premisse, esse requisito regulatório explícito impede a migração.
O sistema fica on-premisse até que a regulação seja revisada ou a instituição obtenha autorização específica. Se ocorrer a migração sem cumprir os requisitos regulatórios, ocorre problema grave de compliance.




Exercício 1.3 — Calculando o impacto do SLA
Sistema de e-commerce com SLA de 99,9%.

a) Quantas horas de downtime por ano? Resposta: 8,76 hora/ano

Fórmula: Downtime anual (horas) = 8.760 * (1 - SLA/100)
Downtime anual (horas) = 8.760 * (1 - 99,9/100)
Downtime anual (horas) = 8.760 * 0,001 
Downtime anual (horas) = 8,76 hora/ano


b) Se processa R$ 50.000/hora em vendas, qual o impacto financeiro máximo por ano? Resposta: Impacto financeiro máximo por ano de R$ 438.000
Impacto financeiro máximo por ano = R$ 50.000/hora * 8,76 horas
Impacto financeiro máximo por ano = 50.000 * 8,76
Impacto financeiro máximo por ano = R$ 438.000


c) Para reduzir o impacto para menos de R$ 50.000/ano, qual SLA mínimo seria necessário? Resposta: Seria necessário um SLA mínimo de 99,99% para conseguir reduzir o impacto financiro do ano.
Considerando que só 1 hora pode ficar fora do total de 8.760 horas:
Impacto financeiro máximo = 50.000

1h /ano = 1 / 8760 = 0,0001142

SLA = 1 - 0,0001142 = 0,9998858
SLA = 99,9886%

Fórmulas úteis: 
Downtime anual (horas) = 8.760 × (1 - SLA/100) 
Downtime mensal (min) = 43.800 × (1 - SLA/100)



Exercício 1.4 — RBAC na prática
Você é o responsável de segurança da Quantum Commerce. Para cada perfil abaixo, escolha a role built-in do Azure mais adequada e justifique:

| Perfil                                                              | Role Axure mais adequada      | Justificativa                                                                                                                                  |
|---------------------------------------------------------------------|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| Agente de IA que LÊ produtos do Storage para responder ao cliente   | Storage Blob Data Reader      | Permissão mínima de leitura em Blob Storage. O agente não precisa escrever e nem gerenciar recursos, princípio do menor privilégio.           |
| Engenheiro de dados que CARREGA novos catálogos no Blob             | Storage Blob Data Contributor | Precisa de leitura e escrita em Blob. Escopo retrito ao storage evitando acesso a outros recursos da assinatura.                              |
| Time de FinOps que precisa VER custos sem alterar recursos          | Cost Management Reader        | Acesso somente de leitura ao Cost Management. Não confere nenhuma permissão sobre recursos de computação ou dados.                            |
| Auditor externo que precisa LER configurações de toda a assinatura  | Reader na assinatura          | Leitura em todos os recursos sem possibilidade de alteração. Escopo de assinatura garante a visibilidade ampla exigida pela auditoria.        |
| Sistema de CI/CD que provisiona infraestrutura via Terraform        | Contributor no Resource Group | PRecisa criar/modificar recursos. Limitar ao Resource Group específico reduz o raio de blast em caso de comprometimento do service principal. |




🔴 Nível 3 — Bônus: 

Exercício 3.3 — Desafio de arquitetura: multi-cloud para a Quantum Commerce
Contexto: O CTO da QC quer evitar lock-in e pediu análise multi-cloud.

a) Desenhe uma arquitetura multi-cloud com pelo menos 2 provedores. Justifique por que cada workload em cada nuvem.

Workload: Agente IA conversacional + RAG
Nuvem: Azure
Justificativa: Azure OpenAI Service (GPT-4o) + Azure AI Search com vector search nativo, melhor integração. SLA corporativo e conformidade LGPD / GPDR.

Workload: Datalake e Analytics BI
Nuvem: AWS
Justificativa: Amaxon S3 + Redshift, ecossistema de analytics e times de BI maduros. Times de dados já treinasoas em AWS.




b) Identifique 4 desafios principais: latência entre nuvens, identidade unificada, custos de egress, observabilidade.

1) Latência entre nuvens Chamadas cross-cloud (Azure - AWS) adicionam de 20 a 80 ms dependnedo das regiões.
A mitigação é manter no mesmo provedor os serviços que se comunicam com alta frequência, reservando o multi-cloud para workloads com acoplamento fraco.

2) Identidade unificada Azure Entra ID e AWS IAM são sistemas independents. A solução é adotar um IdP central com federação para AWS via IAM Identity Center usando OIDC/SAML.

3) Custo de egress transferência de dados entre provedores tem custo direto.
Azure cobra $0,087/GB de saída para internet em 10TV/mês representa $890/mês só de egress. A arquitetura deve minimizar dados cruzando a fronteira entre nuvens.

4) Observabilidade unificada com Logs e traces espalhados entre Azure Monitor e CloudWatch.
A solução é adotar uma ferramenta agnóstica, Datadog, Grafana Cloud ou OpenTelemetry com backend centralizado, realizando a ingestão de ambos os provedores em um único Dash.



c) Compare 2 ferramentas IaC multi-cloud:

Terraform (HashiCorp) — https://www.terraform.io
Pulumi — https://www.pulumi.com
Para cada: linguagem, pricing, suporte aos 3 grandes, quando escolher.

| Critério de comparação    | Terraform (HashiCorp)                                                  | Pulumi                                                                                                                                        |
|---------------------------|------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| Linguagem                 | HCL , DSL própria                                                      | Python, TypeScript, Go, C#                                                                                                                    |
| Pricing                   | Open Source + Terraform Cloud.                                         | Open Source + Pulumi Cloud (freemium).                                                                                                        |
| Suporte Azure x AWS x GCP | Providers maduros nos 3.                                               | Provider maduros nos 3.                                                                                                                       |
| Curva de Aprendizado      | Menor , HCL é simples e direto.                                        | Maior, requer proficiência na linguagem escolhida.                                                                                            |
| Quando escolher           | Padrão de mercado. Times sem experiência em linguagens de programação. | Times de engenharia com experiência em dev. Lógica complexa com loops condicionas, testes unitários de IaC. Preferência por não aprender HCL. |

Para o QC: Terraform é a escolha mais segura para o time atual considerando maior base de módulos prontos, mais fácil de contratar e onboarding mais rápido.
Pulumini seria considerado apenas se o time de plataforma tivesse forte conhecimento em Python e/ou TypeScript, e se precisassem de lógica de provisionamento muito dinâmica.



d) Estime custo de egress: 10 TB/mês entre Azure (Brazil South) e AWS (us-east-1). Consulte tabelas de preço e calcule.

Dica avançada: Pesquise Azure Arc e AWS Outposts — como se encaixariam na QC?

Volume = 10 TB = 2.240 GB

Azure egress: os primeiros 10 GB são gratuítos
10.230 GB * 0,087 = $889,91/mês

AWS ingress: gratuíto

Total egress mensal: $890/ mês
Total anual: $10.680/ ano


Pesquise Azure Arc e AWS Outposts — como se encaixariam na QC?
Azure ARc: permite gerenciar recursos AWS (VMs, clusters K8s) como se fossem recursos Azure através da Azure Policy, Defender for Cloud e Monitor de forma unificada.
Na QC o time de segurança teria um dash único de compliance mesmo com workloads em dois provedores.

AWS Outposts: é hardware AWS instalado em datacenter próprio para workloads com requisitos de ultra-baixa latência ou soberania de dados on-premisse. 
Complementaria o modelo híbrido da QC nos países com restrições regulatórias mais rígidas, onde , por exemplo, os dados financeiros  não podem sair do território nacional.

---

## 🟡 Nível 2 — Respostas + Implementação

(Respostas + diagramas + código quando aplicável)

---

## 🔴 Nível 3 — Bônus (se aplicável)

(Respostas + scripts/links)

---

## Reflexão coletiva

3-5 parágrafos respondendo:

1. O que o grupo aprendeu de mais importante nesta aula?
2. Como isso se conecta com a arquitetura cloud de uma plataforma agentic?
3. Que decisão arquitetural vocês fariam diferente se começassem o projeto QC hoje?

---

## Artefatos do ZIP

- Diagrama: `diagramas/arquitetura-qc-aulaXX.png`
- Código IaC: `terraform/`
- Scripts: `scripts/`
- Endpoint ativo (se houver): URL pública sem credenciais — apenas para demonstração durante a janela de correção
