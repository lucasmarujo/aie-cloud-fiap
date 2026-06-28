"""
Function HTTP da Quantum Commerce — versão L₂ evoluída (Aula 3, N2).

Continua a aplicação da Aula 3 (rotas /produtos e /health, que leem o
produtos.csv do Blob via Managed Identity) e adiciona a SEGUNDA tool do
agente: /calcular_frete (Exercício 2.1).

A regra de frete vive em frete_calc.py (lógica pura, testável offline). A
Function só faz parsing de entrada/saída HTTP — o cálculo não depende de
Storage nem de credencial, então responde mesmo se o Blob estiver indisponível.

Variável de ambiente esperada (configurada pelo Terraform):
    STORAGE_ACCOUNT_AULA2 — Storage Account com o container 'catalogo' (rota /produtos)
App Insights (Exercício 2.2) é injetado pelo Terraform via
    APPLICATIONINSIGHTS_CONNECTION_STRING — não precisa de código aqui.
"""
import csv
import json
import logging
import os

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from frete_calc import FreteError, calcular_frete

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

STORAGE_ACCOUNT = os.environ["STORAGE_ACCOUNT_AULA2"]
CONTAINER       = "catalogo"
BLOB_NAME       = "produtos.csv"

_credential = DefaultAzureCredential()
_blob_service = BlobServiceClient(
    f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=_credential,
)


def carregar_produtos() -> list[dict]:
    """Baixa produtos.csv do Blob e converte em lista de dicts."""
    blob_client = _blob_service.get_blob_client(container=CONTAINER, blob=BLOB_NAME)
    csv_content = blob_client.download_blob().readall().decode("utf-8")
    rows = list(csv.DictReader(csv_content.splitlines()))
    for r in rows:
        r["id"]      = int(r["id"])
        r["preco"]   = float(r["preco"])
        r["estoque"] = int(r["estoque"])
    return rows


def _json_response(payload: dict, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        mimetype="application/json",
        status_code=status,
    )


@app.route(route="produtos", methods=["GET"])
def listar_produtos(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/produtos?categoria=moveis&nome=cadeira (primeira tool)."""
    logging.info("Endpoint /produtos chamado")

    try:
        produtos = carregar_produtos()
    except Exception as e:
        logging.exception("Falha ao carregar produtos do Blob")
        return _json_response({"erro": f"falha ao acessar storage: {e!s}"}, 500)

    categoria = (req.params.get("categoria") or "").lower().strip()
    nome      = (req.params.get("nome")      or "").lower().strip()

    resultado = produtos
    if categoria:
        resultado = [p for p in resultado if p["categoria"].lower() == categoria]
    if nome:
        resultado = [p for p in resultado if nome in p["nome"].lower()]

    return _json_response({"total": len(resultado), "produtos": resultado})


@app.route(route="calcular_frete", methods=["GET", "POST"])
def calcular_frete_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Segunda tool — GET/POST /api/calcular_frete.

    GET:  /api/calcular_frete?cep_origem=01310-100&cep_destino=20040-002&peso=2.5
    POST: body JSON {"cep_origem": "...", "cep_destino": "...", "peso_kg": 2.5}
    """
    logging.info("Endpoint /calcular_frete chamado")

    body: dict = {}
    try:
        body = req.get_json() or {}
    except ValueError:
        body = {}  # GET sem corpo, ou corpo não-JSON

    cep_origem  = req.params.get("cep_origem")  or body.get("cep_origem")
    cep_destino = req.params.get("cep_destino") or body.get("cep_destino")
    peso        = req.params.get("peso") or body.get("peso") or body.get("peso_kg")

    try:
        frete = calcular_frete(cep_origem, cep_destino, peso)
    except FreteError as e:
        logging.warning("Entrada invalida em /calcular_frete: %s", e)
        return _json_response({"erro": str(e)}, 400)

    logging.info(
        "Frete calculado: %s->%s, %.1f km, R$ %.2f",
        frete.cep_origem, frete.cep_destino, frete.distancia_km, frete.valor_frete_brl,
    )
    return _json_response(frete.to_dict())


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return _json_response({
        "status": "ok",
        "service": "qc-catalogo",
        "source": "blob",
        "tools": ["produtos", "calcular_frete"],
    })
