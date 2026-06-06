# Entrega Aula 01 — Grupo NN · Contribuição da Pessoa C

> **Rascunho para merge.** Este arquivo contém só as partes da Pessoa C (N2 → 2.2 e N3 → 3.1 + 3.2),
> escritas no formato do [template oficial](../../../entregas/template-entrega-grupo.md).
> A Pessoa B junta isto ao `entrega-grupo-aula01.md` final quando montar o documento do grupo.

**Linha da Pessoa C para a tabela "Distribuição do trabalho":**

| Membro              | Nível assumido        | Item específico                                        |
|---------------------|-----------------------|--------------------------------------------------------|
| Lucas Marujo Amadeu | 🟡 N2 + 🔴 N3 (bônus) | Exercício 2.2 (custos) + 3.1 (Terraform) + 3.2 (Bicep) |

**Artefatos que a Pessoa C entrega no ZIP:**
- `terraform/` → `main.tf`, `variables.tf`, `outputs.tf`, `terraform.tfvars.example` (Exercício 3.1)
- `bicep/main.bicep` (Exercício 3.2)
- `README.md` → como rodar o N3 (Terraform + Bicep) e limpar tudo

---

## 🟡 Nível 2 — Exercício 2.2 — Comparativo de custos (3 provedores)

### Premissas (para a comparação ser honesta)

Preços **de tabela _on-demand_** consultados nas páginas oficiais dos provedores (jun/2026), Linux, em USD, regiões **Azure East US / AWS us-east-1 / GCP us-central1**. Base de **730 horas/mês** (convenção das três calculadoras). Os valores batem com as calculadoras oficiais; mesmo assim, vale anexar um print/export na entrega final, porque preço de nuvem muda com frequência.

- **Compute:** instância _general purpose_ de 2 vCPU / 8 GB, ligada 24/7.
- **Storage:** 500 GB de _object storage_ tier padrão/quente, redundância local (LRS/regional). Sem custo de transação/egress (some 30–70% no mundo real).
- **Banco:** PostgreSQL **gerenciado**, 2 vCPU / 8 GB + 100 GB de disco, **zonal / single-AZ** (sem réplica de HA — HA ~dobra o preço do banco nas três).
- **Serverless:** 10 milhões de execuções/mês, **512 MB** e **~200 ms** por execução (= 1.000.000 GB-segundos). Sem abater a camada gratuita mensal (deixa a comparação justa entre os três).

### Memória de cálculo (taxas unitárias usadas)

| Recurso | Azure | AWS | GCP |
|---------|-------|-----|-----|
| VM 2vCPU/8GB (US$/h) | D2s_v3 — **0,096** | m5.large — **0,096** | e2-standard-2 — **0,067** |
| Object storage (US$/GB-mês) | Blob Hot LRS — **0,018** | S3 Standard — **0,023** | Cloud Storage Standard — **0,020** |
| Banco — compute | PG Flexible GP 2vCore ≈ **0,144/h** | RDS db.m5.large — **0,192/h** | Cloud SQL: **0,0413/vCPU-h + 0,007/GB-h** |
| Banco — storage (US$/GB-mês) | **0,115** | gp3 — **0,115** | SSD — **0,17** |
| Serverless | exec **0,20/M** + **0,000016**/GB-s | exec **0,20/M** + **0,00001667**/GB-s | exec **0,40/M** (2M grátis) + CPU/mem (1ª gen) |

### Tabela comparativa (totais)

| Item | Azure | AWS | GCP | Tipo / cálculo |
|------|-------|-----|-----|----------------|
| 2 × VM (2 vCPU / 8 GB) | US$ 140 | US$ 140 | US$ 98 | `0,096×730×2` · `0,096×730×2` · `0,067×730×2` |
| 500 GB object storage | US$ 9 | US$ 12 | US$ 10 | `500 × {0,018 / 0,023 / 0,020}` |
| Banco gerenciado (2vCPU/8GB + 100GB) | US$ 117 | US$ 152 | US$ 118 | compute + 100GB de disco (ver memória de cálculo) |
| 10M req serverless | US$ 18 | US$ 19 | US$ 22 | Functions Consumption · Lambda · Cloud Functions |
| **Total mensal** | **≈ US$ 284** | **≈ US$ 322** | **≈ US$ 248** | — |
| **Total anual** | **≈ US$ 3.405** | **≈ US$ 3.864** | **≈ US$ 2.972** | `mensal × 12` |

> Detalhe do banco: **Azure** ≈ US$ 105 compute + US$ 11,50 storage; **AWS** ≈ US$ 140 compute (db.m5.large a US$ 0,192/h é o "imposto RDS", ~2× a EC2 equivalente) + US$ 11,50 storage; **GCP** ≈ US$ 101 compute (`2×0,0413 + 8×0,007 = 0,1386/h`) + US$ 17 storage SSD.

### Análise

**a) Qual ficou mais barato? A diferença é significativa?**
**GCP**, com **≈ US$ 248/mês** — cerca de **13% abaixo do Azure** (US$ 284) e **23% abaixo da AWS** (US$ 322). A diferença vem de duas frentes: o **compute** (a `e2-standard-2` a US$ 0,067/h é ~30% mais barata que as concorrentes a US$ 0,096/h — a família E2 já nasce com preço otimizado) e o **banco** (a AWS cobra um prêmio claro pelo RDS: db.m5.large a US$ 0,192/h, o dobro da EC2 `m5.large`). Storage e serverless são ruído neste volume (somam ~US$ 30/mês nos três). A diferença anualizada é real (~US$ 890/ano entre GCP e AWS), mas **não é ordem de grandeza** — para um time pequeno, os fatores não-financeiros do item (c) pesam mais que esses 13–23%.

**b) Aplicando Reserved Instances de 1 ano no mais caro (AWS), muda?**
Muda o ranking. O custo da AWS é dominado por compute + banco rodando 24/7 — o cenário ideal de reserva. Com _commitment_ de 1 ano (Standard RI, no-upfront, ~35–39% de desconto):
- 2 × m5.large reservadas: de ~US$ 140 → **~US$ 86/mês**
- RDS db.m5.large reservada: de ~US$ 140 → **~US$ 89/mês** (+ US$ 11,50 storage)
- Storage S3 (US$ 11,50) e serverless (US$ 19) seguem iguais
- **Novo total AWS ≈ US$ 217/mês** (anual ~US$ 2.600) — queda de ~33%

Isso **inverte o pódio**: a AWS reservada (US$ 217) passa o GCP _on-demand_ (US$ 248) e o Azure _on-demand_ (US$ 284). A leitura justa, porém, é que **as três** oferecem 1 ano de compromisso (Azure Reserved Instances / Savings Plans, GCP Committed Use Discounts) com desconto parecido (~30–40%). Ou seja: se reservar uma, reserve as três — e o ranking provavelmente volta a **GCP < Azure < AWS**, todas ~1/3 mais baratas. **Lição prática:** workload estável 24/7 nunca deveria ficar em _on-demand_; reserva é dinheiro na mesa.

**c) Que outros fatores você consideraria para um projeto de IA?**
Preço é o critério mais fácil de medir e o menos decisivo. Para AI Engineering eu olharia, em ordem:
1. **Serviços de IA gerenciados e modelos** — Azure OpenAI / AI Foundry, AWS Bedrock, GCP Vertex AI. Qual tem os modelos que preciso, com a maturidade e os limites de cota certos?
2. **Disponibilidade e cota de GPU** (e preço de _spot_ para treino) — costuma ser o real gargalo, não a VM.
3. **Vector DB / busca semântica nativa** (Azure AI Search, etc.) — peça central de RAG.
4. **Data gravity e egress** — onde o dado já vive? Tirar TBs de uma nuvem para outra é caro e lento (ver Exercício 3.3 da Pessoa A).
5. **Região e compliance (LGPD)** — o serviço de IA existe em Brazil South? Posso manter dados de cliente no país?
6. **Maturidade de IaC, ecossistema e _skills_ do time** — não adianta ser 13% mais barato se o time perde semanas aprendendo a stack.
7. **Identidade e segurança gerenciadas** (Managed Identity / IAM) — liga direto no RBAC do Exercício 1.4.

> Conexão com a QC: a arquitetura da Pessoa B (Ex. 2.1) define **quais** serviços entram; este comparativo dá a **ordem de grandeza do custo** de rodar o esqueleto — e mostra que, para a QC (12 países, 5M SKUs, IA conversacional), a conta real vai ser dominada por GPU/serviços cognitivos e egress, não pela VM do lab.

**Fontes (preços consultados em jun/2026):** [Azure VM Linux](https://azure.microsoft.com/en-us/pricing/details/virtual-machines/linux/) · [AWS EC2 On-Demand](https://aws.amazon.com/ec2/pricing/on-demand/) · [GCP Compute Engine (e2-standard-2)](https://www.economize.cloud/resources/gcp/pricing/compute-engine/e2-standard-2/) · [Azure Blob](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/) · [AWS RDS PostgreSQL](https://aws.amazon.com/rds/postgresql/pricing/) · [Azure DB for PostgreSQL Flexible Server](https://azure.microsoft.com/en-us/pricing/details/postgresql/flexible-server/) · [GCP Cloud SQL](https://cloud.google.com/sql/pricing). Recalcule na calculadora oficial ([Azure](https://azure.microsoft.com/pricing/calculator) · [AWS](https://calculator.aws) · [GCP](https://cloud.google.com/products/calculator)) antes do envio.

---

## 🔴 Nível 3 — Exercício 3.1 — Terraform: endurecer a segurança de rede

**Código:** `terraform/` (`main.tf`, `variables.tf`, `outputs.tf`, `terraform.tfvars.example`). **Como rodar:** ver `README.md`.

Parti do `main.tf` do lab (Atividade 5) e fiz as quatro mudanças pedidas:

1. **SSH não fica mais aberto para o mundo.** A regra `SSH` do NSG saiu de `source_address_prefix = "*"` para `"${var.meu_ip}/32"`. O IP vem de uma **variável** `meu_ip` (sem _default_, com `validation` de formato IPv4), preenchida via `terraform.tfvars` a partir de `curl -s ifconfig.me`. Nada de hardcode e nada de segredo no código.
2. **Segunda subnet `subnet-app` (`10.0.2.0/24`)** na mesma VNet, como fundação para isolar a futura camada de aplicação da QC da subnet de gestão/SSH.
3. **Output do IP público** (`public_ip_address`) confirmado — e adicionei `ssh_allowed_from` e `subnets` como _outputs_ de verificação, para evidenciar no `apply` que a porta 22 está travada no meu `/32` e que as duas subnets existem.
4. **Diff do `terraform plan`** — partindo do código original, o plano traz **somente**:

| Símbolo | Recurso | Mudança |
|---------|---------|---------|
| `~` _update in-place_ | `azurerm_network_security_group.nsg` | regra `SSH`: `source_address_prefix` `"*"` → `"<meu_ip>/32"` |
| `+` _create_ | `azurerm_subnet.app` | nova subnet `subnet-app` (`10.0.2.0/24`) |

**A VM não é recriada.** `azurerm_linux_virtual_machine.vm` nem aparece no diff — alterar uma regra de NSG e adicionar uma subnet são operações de rede que não tocam o ciclo de vida da VM. É exatamente o comportamento que o item 4 pede para demonstrar (mudança cirúrgica, sem _downtime_ de recriar a máquina).

**Boas práticas aplicadas (Critério 3 — qualidade técnica):** sem segredos no código (IP via _tfvars_, chave SSH via `file()`), variável com `validation`, comentários marcando cada mudança `[3.1 — item N]`, e `terraform.tfvars.example` versionado em vez do `terraform.tfvars` real.

---

## 🔴 Nível 3 — Exercício 3.2 — Bicep equivalente

**Código:** `bicep/main.bicep`. **Deploy e comparação:** ver `README.md`.

Como este repositório **não traz o `template.json` ARM** pronto, escrevi o `main.bicep` diretamente a partir do Terraform endurecido (o enunciado permite os dois caminhos) e **gerei o `template.json` com `bicep build` só para a contagem de linhas**. O Bicep provisiona os mesmos recursos: VNet + 2 subnets (`default` + `subnet-app`) + NSG (SSH travado no meu IP, HTTPS, HTTP) + IP público Standard + NIC + VM Ubuntu 24.04 — e expõe os mesmos outputs.

### Comparação dos artefatos (item 4)

| Artefato | Linhas | Observação |
|----------|--------|------------|
| `template.json` (ARM) | **248** | Gerado com `bicep build main.bicep --outfile main.json` no Cloud Shell |
| `main.tf` (Terraform, só o arquivo) | **173** | Versão endurecida do 3.1 (com comentários) |
| `terraform/` (módulo completo: main+variables+outputs) | **258** | Base mais justa contra um Bicep que junta params+recursos+outputs |
| `main.bicep` | **207** | Arquivo único (params + recursos + outputs) |

> Na comparação de **arquivo único** (o que o enunciado pede): `main.tf` **173** < `main.bicep` **207** < `template.json` ARM **248**. O ARM é a saída compilada do `bicep build` — sem um único comentário e cheio de `[resourceId(...)]`; ou seja, é ao mesmo tempo o **mais longo e o menos legível**. Como as contagens de TF e Bicep ainda incluem comentários, no "só código" a vantagem dos dois sobre o ARM é ainda maior.

### Respostas

**Qual ficou mais legível para mim?**
Ranking claro: **Bicep ≈ Terraform ≫ ARM JSON**. O ARM JSON é verboso e cheio de aninhamento — difícil de ler e revisar. Entre Bicep e Terraform, para **esta VM** achei o **Terraform um pouco mais enxuto**: o recurso `azurerm_linux_virtual_machine` "achata" as _nested properties_ (`osProfile`, `storageProfile`, `networkProfile`) que no Bicep ainda aparecem aninhadas, herança do modelo ARM. Mas o Bicep é absurdamente melhor que o JSON cru e tem uma vantagem real: **não exige _provider_ nem gerenciar _state file_**.

**Em que cenário eu escolheria Bicep sobre Terraform?**
- Ambiente **100% Azure**, sem multi-cloud no horizonte.
- Quero ferramenta **nativa Microsoft**: suporte _day-0_ de recursos novos (não dependo do _provider_ `azurerm` ser atualizado), integração direta com `az`, Azure Policy e `what-if`.
- Não quero **gerenciar _state_** — o Bicep usa o histórico de _deployment_ do próprio ARM como estado, eliminando o `terraform.tfstate` (e o risco de vazar segredo nele) e o _remote backend_.
- Time já vive em **Azure DevOps / ecossistema Azure**.

**Quando eu ficaria no Terraform:** multi-cloud (a QC pode ir multi-nuvem — ver 3.3 da Pessoa A), necessidade de **módulos reutilizáveis** e _registry_, `plan` explícito como _gate_ de revisão, e o ecossistema/comunidade maior. Para a trajetória da QC ao longo das 6 aulas, **Terraform** segue como a escolha principal; o Bicep entra como alternativa nativa quando algum bloco for exclusivamente Azure.

---

## 💭 Insumo da Pessoa C para a reflexão coletiva (para a Pessoa B consolidar)

Um parágrafo, do ângulo de infra/custos, para a Pessoa B encaixar na reflexão final:

> O que mais marcou na minha parte foi perceber que **IaC é o que torna um agente reprodutível**. Travar o SSH no meu IP via uma variável (em vez de `*` hardcoded) e versionar o `.example` em vez do `.tfvars` é o mesmo princípio que vamos precisar para os agentes da QC: **provisionamento determinístico e segredos fora do código**. No comparativo de custos ficou claro também que, para IA, a conta não é dominada pela VM, e sim por GPU, serviços cognitivos e egress — então decisão de arquitetura e de _FinOps_ andam juntas desde o dia 1. Se recomeçássemos hoje, já nasceria com Reserved/Committed Use no compute estável e _state_ remoto para o Terraform.
