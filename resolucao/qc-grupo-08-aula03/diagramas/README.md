# Diagramas — Aula 3

## `appinsights-live-metrics.png` (Exercício 2.2.b)

Print **a capturar no seu apply**, durante a execução de `scripts/gerar_carga.py`:

1. Portal Azure → o Application Insights `appi-qc-<sufixo>` (output `app_insights_name`).
2. Aba **Live Metrics**.
3. Rode `python scripts/gerar_carga.py "$HOST"` e tire o print enquanto as
   barras de *Incoming Requests* / *Request Duration* / *Request Rate* sobem.
4. Salve o print aqui como `appinsights-live-metrics.png`.

## `arquitetura-qc-aula03.png`

Diagrama consolidado da arquitetura da QC com a **camada de API/compute** desta
aula (Function + Container Apps como hosts das tools do agente). É um artefato
do **grupo** (montado junto com N1 + N3 no `entrega-grupo-aula03.md` final).
A visão específica da N2 está como diagrama Mermaid dentro de
[`../respostas-N2-aula03.md`](../respostas-N2-aula03.md).
