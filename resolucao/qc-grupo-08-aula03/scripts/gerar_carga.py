#!/usr/bin/env python3
"""
Gera carga variada contra a Function da QC — Exercício 2.2 (App Insights).

Faz 20 chamadas distribuídas entre as rotas /health, /produtos e
/calcular_frete, incluindo PROPOSITALMENTE algumas requisições inválidas
(CEP malformado, peso ausente), para popular o **Failures blade** e o
**Live Metrics** do Application Insights.

Mede a latência cliente-side de cada chamada e imprime p50/p95/p99 + taxa de
erro — os mesmos números que você confere depois no AI (Performance/Failures).

Uso (no Cloud Shell, após o deploy da Function):

    FUNC_NAME=$(terraform output -raw function_app_name)
    python scripts/gerar_carga.py "https://$FUNC_NAME.azurewebsites.net"

Sem dependências externas — usa apenas a stdlib (urllib), roda em qualquer
Python 3.8+.
"""
import json
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT_S = 30

# (rota, querystring, espera_sucesso?) — 20 chamadas, ~15% de falhas propositais
PLANO = [
    ("health",         {},                                                             True),
    ("produtos",       {"categoria": "moveis"},                                        True),
    ("produtos",       {"categoria": "eletronicos"},                                   True),
    ("produtos",       {"categoria": "cozinha"},                                       True),
    ("produtos",       {"nome": "cadeira"},                                            True),
    ("produtos",       {"nome": "fone"},                                               True),
    ("produtos",       {},                                                             True),
    ("calcular_frete", {"cep_origem": "01310-100", "cep_destino": "20040-002", "peso": "2.5"}, True),
    ("calcular_frete", {"cep_origem": "01310-100", "cep_destino": "60160-230", "peso": "8"},   True),
    ("calcular_frete", {"cep_origem": "01310-100", "cep_destino": "90010-150", "peso": "3"},   True),
    ("calcular_frete", {"cep_origem": "01310-100", "cep_destino": "30130-110", "peso": "1.2"}, True),
    ("calcular_frete", {"cep_origem": "01310-100", "cep_destino": "40010-000", "peso": "5"},   True),
    ("calcular_frete", {"cep_origem": "01310-100", "cep_destino": "05424-150", "peso": "0.5"}, True),
    ("produtos",       {"categoria": "moveis", "nome": "mesa"},                        True),
    ("health",         {},                                                             True),
    ("calcular_frete", {"cep_origem": "01310-100", "cep_destino": "69005-040", "peso": "12"},  True),
    # --- falhas propositais (popular o Failures blade) ---
    ("calcular_frete", {"cep_origem": "abc", "cep_destino": "20040-002", "peso": "2"},  False),  # CEP inválido -> 400
    ("calcular_frete", {"cep_origem": "01310-100", "cep_destino": "20040-002"},         False),  # peso ausente -> 400
    ("calcular_frete", {"cep_origem": "01310-100", "cep_destino": "20040-002", "peso": "-3"}, False),  # peso <= 0 -> 400
    ("naoexiste",      {},                                                             False),  # rota inexistente -> 404
]


def chamar(base: str, rota: str, params: dict):
    url = f"{base.rstrip('/')}/api/{rota}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_S) as resp:
            resp.read()
            status = resp.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:  # noqa: BLE001 — timeout, DNS, conexão
        return (None, time.perf_counter() - inicio, f"EXC {type(e).__name__}")
    return (status, time.perf_counter() - inicio, None)


def main() -> int:
    if len(sys.argv) < 2:
        print("uso: python gerar_carga.py https://<func>.azurewebsites.net", file=sys.stderr)
        return 2
    base = sys.argv[1]

    latencias_ms: list[float] = []
    erros_inesperados = 0
    print(f"→ Disparando {len(PLANO)} chamadas contra {base}\n")
    print(f"{'#':>2} {'rota':<16} {'status':>6} {'ms':>8}  obs")
    print("-" * 56)

    for i, (rota, params, espera_ok) in enumerate(PLANO, 1):
        status, dt, exc = chamar(base, rota, params)
        ms = dt * 1000
        latencias_ms.append(ms)
        ok_real = exc is None and 200 <= (status or 0) < 400
        # "inesperado" = resultado diferente do planejado (sucesso que falhou, etc.)
        inesperado = ok_real != espera_ok
        if inesperado:
            erros_inesperados += 1
        marca = "" if not inesperado else "  <-- INESPERADO"
        obs = exc or ("ok" if ok_real else "falha-esperada" if not espera_ok else "FALHA")
        print(f"{i:>2} {rota:<16} {str(status or '-'):>6} {ms:>8.0f}  {obs}{marca}")

    print("-" * 56)
    lat = sorted(latencias_ms)
    falhas_planejadas = sum(1 for _, _, ok in PLANO if not ok)
    print(
        f"\nChamadas: {len(lat)} | "
        f"falhas planejadas: {falhas_planejadas} ({falhas_planejadas/len(lat):.0%}) | "
        f"resultados inesperados: {erros_inesperados}"
    )
    print(
        f"Latencia (ms): media={statistics.mean(lat):.0f}  "
        f"p50={_pct(lat,50):.0f}  p95={_pct(lat,95):.0f}  p99={_pct(lat,99):.0f}  "
        f"max={lat[-1]:.0f}"
    )
    print(
        "\nAgora abra o portal -> Application Insights -> Live Metrics (durante a carga)\n"
        "e o Failures blade para confirmar as 4 falhas propositais (3x HTTP 400 + 1x 404)."
    )
    return 0


def _pct(ordenado: list[float], p: float) -> float:
    if not ordenado:
        return 0.0
    k = (len(ordenado) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(ordenado) - 1)
    return ordenado[f] + (ordenado[c] - ordenado[f]) * (k - f)


if __name__ == "__main__":
    raise SystemExit(main())
