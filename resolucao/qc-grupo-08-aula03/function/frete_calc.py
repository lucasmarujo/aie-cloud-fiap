"""
Cálculo de frete determinístico da Quantum Commerce — Exercício 2.1 (N2, Aula 3).

Lógica PURA, sem I/O e sem dependências externas (apenas stdlib), para que:
  - a Function HTTP `calcular_frete` a importe sem overhead nem cold start extra;
  - os testes (pytest) rodem offline, sem Azure;
  - o script de linha de comando (scripts/calcular_frete_local.py) exercite
    exatamente a mesma regra de negócio.

Modelo de distância (didático): o Brasil é dividido em 10 macrorregiões pelo
PRIMEIRO dígito do CEP. Cada região recebe o centroide aproximado (lat/lon) da
sua capital de referência. A distância entre dois CEPs é a de Haversine entre
os centroides; para CEPs da mesma macrorregião usa-se uma estimativa
intrarregional determinística a partir dos dígitos seguintes.

⚠️  Em produção a distância viria de um geocoder real (API dos Correios,
Azure Maps / Google Maps). Aqui o objetivo é uma regra DETERMINÍSTICA e
testável, como pede o enunciado ("cálculo simples ... pode ser determinístico").
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

# Centroides aproximados (lat, lon) por primeiro dígito do CEP.
# Fonte: faixas oficiais de CEP dos Correios + coordenadas das capitais.
REGIOES_CEP: dict[str, tuple[float, float]] = {
    "0": (-23.5505, -46.6333),  # SP — capital e Grande SP
    "1": (-22.9056, -47.0608),  # SP — interior e litoral (Campinas)
    "2": (-22.9068, -43.1729),  # RJ / ES (Rio de Janeiro)
    "3": (-19.9167, -43.9345),  # MG (Belo Horizonte)
    "4": (-12.9777, -38.5016),  # BA / SE (Salvador)
    "5": (-8.0476, -34.8770),   # PE / AL / PB / RN (Recife)
    "6": (-3.7319, -38.5267),   # CE / PI / MA / Norte (Fortaleza)
    "7": (-15.7939, -47.8828),  # DF / GO / TO / MT / MS / RO (Brasília)
    "8": (-25.4284, -49.2733),  # PR / SC (Curitiba)
    "9": (-30.0346, -51.2177),  # RS (Porto Alegre)
}

# Tabela de tarifas (R$) — simples e determinística, como pede o enunciado.
TARIFA_BASE_BRL = 8.50       # custo fixo de manuseio/coleta
TARIFA_POR_KM_BRL = 0.012    # componente de distância (R$ por km)
TARIFA_POR_KG_BRL = 1.20     # componente de peso (R$ por kg)
RAIO_TERRA_KM = 6371.0

VELOCIDADE_KM_POR_DIA = 500  # deslocamento médio rodoviário por dia útil
DIAS_PROCESSAMENTO = 1       # separação + postagem
PESO_MAXIMO_KG = 100.0       # acima disso vira frete dedicado (fora do escopo)


class FreteError(ValueError):
    """Erro de validação de entrada do cálculo de frete (vira HTTP 400)."""


@dataclass(frozen=True)
class Frete:
    cep_origem: str
    cep_destino: str
    peso_kg: float
    distancia_km: float
    valor_frete_brl: float
    prazo_dias_uteis: int

    def to_dict(self) -> dict:
        return {
            "cep_origem": self.cep_origem,
            "cep_destino": self.cep_destino,
            "peso_kg": round(self.peso_kg, 3),
            "distancia_km": round(self.distancia_km, 1),
            "valor_frete": round(self.valor_frete_brl, 2),
            "moeda": "BRL",
            "prazo_dias_uteis": self.prazo_dias_uteis,
            "metodo": "estimativa-deterministica-regional",
        }


def normalizar_cep(cep) -> str:
    """Remove tudo que não é dígito e valida 8 dígitos.

    Aceita '01310-100', '01310100' ou '  01310 100 '. Lança FreteError se inválido.
    """
    if cep is None:
        raise FreteError("CEP ausente")
    digitos = re.sub(r"\D", "", str(cep))
    if len(digitos) != 8:
        raise FreteError(f"CEP invalido: {cep!r} (esperado 8 digitos)")
    return digitos


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * RAIO_TERRA_KM * math.asin(math.sqrt(h))


def estimar_distancia_km(cep_origem, cep_destino) -> float:
    """Distância determinística (km) entre dois CEPs pelo modelo regional."""
    o = normalizar_cep(cep_origem)
    d = normalizar_cep(cep_destino)
    dist = _haversine_km(REGIOES_CEP[o[0]], REGIOES_CEP[d[0]])
    if o[0] == d[0]:
        # Mesma macrorregião: estimativa intrarregional determinística a partir
        # dos dígitos 2-4 (sub-região). Variação previsível e limitada (~8–158 km).
        sub_o = int(o[1:4])
        sub_d = int(d[1:4])
        dist = 8.0 + abs(sub_o - sub_d) * 0.15
    return dist


def calcular_frete(cep_origem, cep_destino, peso_kg) -> Frete:
    """Calcula valor (R$) e prazo (dias úteis) do frete. Núcleo da tool."""
    try:
        peso = float(peso_kg)
    except (TypeError, ValueError):
        raise FreteError(f"peso invalido: {peso_kg!r}")
    if not math.isfinite(peso) or peso <= 0:
        raise FreteError("peso deve ser > 0 kg")
    if peso > PESO_MAXIMO_KG:
        raise FreteError(f"peso acima do limite de {PESO_MAXIMO_KG:.0f} kg")

    o = normalizar_cep(cep_origem)
    d = normalizar_cep(cep_destino)
    distancia = estimar_distancia_km(o, d)

    valor = TARIFA_BASE_BRL + distancia * TARIFA_POR_KM_BRL + peso * TARIFA_POR_KG_BRL
    prazo = math.ceil(distancia / VELOCIDADE_KM_POR_DIA) + DIAS_PROCESSAMENTO

    return Frete(
        cep_origem=o,
        cep_destino=d,
        peso_kg=peso,
        distancia_km=distancia,
        valor_frete_brl=round(valor, 2),
        prazo_dias_uteis=max(prazo, 1),
    )
