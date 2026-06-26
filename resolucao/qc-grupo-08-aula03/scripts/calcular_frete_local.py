#!/usr/bin/env python3
"""
Exercita a MESMA regra de frete da Function, offline (sem Azure).

Uso:
    # tabela de exemplos (vários destinos a partir do CD da QC em SP):
    python scripts/calcular_frete_local.py

    # cálculo pontual:
    python scripts/calcular_frete_local.py 01310-100 60160-230 3.2

Serve para validar a lógica de frete_calc.py antes do deploy e para conferir
manualmente os números que a tool retornará ao agente.
"""
import os
import sys

# Importa frete_calc.py da pasta ../function (lógica compartilhada com a Function)
_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, "..", "function"))

from frete_calc import FreteError, calcular_frete  # noqa: E402

CD_SP = "01310-100"  # centro de distribuição de referência (Av. Paulista)

EXEMPLOS = [
    ("Sao Paulo (intrarregional)", CD_SP, "05424-150", 1.5),
    ("Rio de Janeiro",             CD_SP, "20040-002", 2.0),
    ("Belo Horizonte",             CD_SP, "30130-110", 2.0),
    ("Salvador",                   CD_SP, "40010-000", 5.0),
    ("Recife",                     CD_SP, "50010-000", 5.0),
    ("Fortaleza",                  CD_SP, "60160-230", 8.0),
    ("Porto Alegre",               CD_SP, "90010-150", 3.0),
    ("Manaus/Norte (faixa 6)",     CD_SP, "69005-040", 12.0),
]


def _tabela() -> int:
    print(f"{'Destino':<26} {'CEP':<10} {'kg':>5} {'dist_km':>9} {'frete_R$':>10} {'prazo':>6}")
    print("-" * 72)
    for rotulo, origem, destino, peso in EXEMPLOS:
        f = calcular_frete(origem, destino, peso)
        print(
            f"{rotulo:<26} {destino:<10} {peso:>5.1f} "
            f"{f.distancia_km:>9.1f} {f.valor_frete_brl:>10.2f} {f.prazo_dias_uteis:>4}d"
        )
    print("\nObs.: distância é estimativa regional determinística (ver frete_calc.py).")
    return 0


def _pontual(origem: str, destino: str, peso: str) -> int:
    try:
        f = calcular_frete(origem, destino, peso)
    except FreteError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1
    import json
    print(json.dumps(f.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        raise SystemExit(_tabela())
    if len(args) != 3:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(_pontual(args[0], args[1], args[2]))
