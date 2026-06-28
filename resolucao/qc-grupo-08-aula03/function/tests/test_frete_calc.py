"""
Testes do cálculo de frete (Exercício 2.1) — rodam offline, sem Azure.

    cd function && python -m pytest -q
    # ou, sem pytest instalado:
    cd function && python tests/test_frete_calc.py

Cobrem: normalização de CEP, validação de entrada, determinismo e as duas
propriedades que importam para o negócio (mais longe => mais caro; mais pesado
=> mais caro).
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frete_calc import (  # noqa: E402
    FreteError,
    calcular_frete,
    estimar_distancia_km,
    normalizar_cep,
)

CD_SP   = "01310-100"  # Av. Paulista (centro de distribuição da QC)
RJ      = "20040-002"  # Centro, Rio de Janeiro
FORTAL  = "60160-230"  # Fortaleza/CE (bem mais longe)
SP_ZONA = "05424-150"  # Pinheiros, mesma macrorregião do CD


def test_normalizar_cep_aceita_formatos():
    assert normalizar_cep("01310-100") == "01310100"
    assert normalizar_cep("01310100") == "01310100"
    assert normalizar_cep(" 01310 100 ") == "01310100"


@pytest.mark.parametrize("ruim", ["", "123", "0131010", "013101000", None, "abcdefgh"])
def test_normalizar_cep_rejeita_invalido(ruim):
    with pytest.raises(FreteError):
        normalizar_cep(ruim)


def test_determinismo():
    a = calcular_frete(CD_SP, RJ, 2.5).to_dict()
    b = calcular_frete(CD_SP, RJ, 2.5).to_dict()
    assert a == b


def test_mais_longe_e_mais_caro():
    perto = calcular_frete(CD_SP, RJ, 2.0)
    longe = calcular_frete(CD_SP, FORTAL, 2.0)
    assert longe.distancia_km > perto.distancia_km
    assert longe.valor_frete_brl > perto.valor_frete_brl
    assert longe.prazo_dias_uteis >= perto.prazo_dias_uteis


def test_mais_pesado_e_mais_caro():
    leve  = calcular_frete(CD_SP, RJ, 1.0)
    pesado = calcular_frete(CD_SP, RJ, 10.0)
    assert pesado.valor_frete_brl > leve.valor_frete_brl
    # peso não muda distância nem prazo
    assert pesado.distancia_km == leve.distancia_km
    assert pesado.prazo_dias_uteis == leve.prazo_dias_uteis


def test_mesma_regiao_tem_distancia_curta():
    intra = estimar_distancia_km(CD_SP, SP_ZONA)
    inter = estimar_distancia_km(CD_SP, RJ)
    assert 0 < intra < 160     # estimativa intrarregional limitada
    assert inter > intra       # cruzar macrorregião é sempre maior


@pytest.mark.parametrize("peso", [0, -1, "abc", None, 101])
def test_peso_invalido_lanca(peso):
    with pytest.raises(FreteError):
        calcular_frete(CD_SP, RJ, peso)


def test_estrutura_da_resposta():
    d = calcular_frete(CD_SP, RJ, 2.5).to_dict()
    assert set(d) == {
        "cep_origem", "cep_destino", "peso_kg", "distancia_km",
        "valor_frete", "moeda", "prazo_dias_uteis", "metodo",
    }
    assert d["moeda"] == "BRL"
    assert d["cep_origem"] == "01310100"
    assert isinstance(d["valor_frete"], float)
    assert d["prazo_dias_uteis"] >= 1


if __name__ == "__main__":  # permite rodar sem pytest instalado
    raise SystemExit(pytest.main([__file__, "-q"]))
