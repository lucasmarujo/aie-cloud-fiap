#!/usr/bin/env python3
# =============================================================================
# Exercício 3.2 (N3 bônus) — Gerador de logs de compras da Quantum Commerce
# -----------------------------------------------------------------------------
# Gera 3 arquivos CSV (jan/fev/mar de 2026), 1000 registros cada, simulando o
# clickstream/log analítico de pedidos da QC. Em seguida (opcional) faz upload
# para o filesystem 'logs' da conta ADLS Gen2 (HNS) provisionada em synapse.tf,
# onde o Synapse Serverless SQL Pool os consulta via OPENROWSET(BULK ...).
#
# Política "no install" do Cloud Shell: usa só a stdlib para gerar os CSVs.
# O upload depende de azure-storage-blob + azure-identity, que já vêm no
# Cloud Shell. Sem credenciais/SDK, o script apenas grava os CSVs localmente.
#
# Uso:
#   python gerar_logs_compras.py                      # só gera os CSVs locais
#   python gerar_logs_compras.py --upload \
#       --account stqclakeXXXXXX --filesystem logs    # gera e sobe ao Lake
#
# Schema (colunas) — alinhado ao WITH(...) da query do Serverless:
#   pedido_id     INT
#   periodo       DATE    (YYYY-MM-DD)  <- usada no GROUP BY CAST(periodo AS DATE)
#   cliente_id    INT
#   categoria     VARCHAR
#   uf            VARCHAR(2)
#   canal         VARCHAR   (web/app/marketplace)
#   qtd_itens     INT
#   valor         DECIMAL(10,2)         <- usada no SUM(valor)
# =============================================================================

import argparse
import calendar
import csv
import os
import random
from datetime import date

SEED = 42  # determinístico: reexecuções geram os mesmos números (reprodutível)
REGISTROS_POR_ARQUIVO = 1000
ANO = 2026

# (mes_numero, sufixo_arquivo)
MESES = [(1, "jan"), (2, "fev"), (3, "mar")]

CATEGORIAS = [
    "eletronicos", "moda", "casa", "livros",
    "esporte", "beleza", "games", "mercado",
]
UFS = ["SP", "RJ", "MG", "RS", "PR", "BA", "SC", "PE", "CE", "GO"]
CANAIS = ["web", "app", "marketplace"]

# Ticket médio plausível por categoria (R$): faixa (min, max) do valor unitário
FAIXA_VALOR = {
    "eletronicos": (200.0, 4500.0),
    "moda":        (40.0, 600.0),
    "casa":        (60.0, 2500.0),
    "livros":      (25.0, 180.0),
    "esporte":     (50.0, 1200.0),
    "beleza":      (20.0, 400.0),
    "games":       (90.0, 3500.0),
    "mercado":     (15.0, 350.0),
}


def gerar_registros(mes: int, n: int, pedido_inicial: int):
    """Gera n registros de compra para um mês de 2026."""
    dias_no_mes = calendar.monthrange(ANO, mes)[1]
    registros = []
    for i in range(n):
        pedido_id = pedido_inicial + i
        # Distribui os pedidos ao longo de todos os dias do mês.
        dia = random.randint(1, dias_no_mes)
        periodo = date(ANO, mes, dia).isoformat()  # YYYY-MM-DD
        categoria = random.choice(CATEGORIAS)
        vmin, vmax = FAIXA_VALOR[categoria]
        qtd_itens = random.randint(1, 5)
        # valor do pedido = (valor unitário aleatório) * qtd, em 2 casas decimais
        valor_unit = random.uniform(vmin, vmax)
        valor = round(valor_unit * qtd_itens, 2)
        registros.append({
            "pedido_id": pedido_id,
            "periodo": periodo,
            "cliente_id": random.randint(1000, 99999),
            "categoria": categoria,
            "uf": random.choice(UFS),
            "canal": random.choice(CANAIS),
            "qtd_itens": qtd_itens,
            "valor": f"{valor:.2f}",
        })
    return registros


def escrever_csv(caminho: str, registros: list):
    campos = ["pedido_id", "periodo", "cliente_id", "categoria",
              "uf", "canal", "qtd_itens", "valor"]
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()  # FIRSTROW=2 na query pula esta linha de header
        writer.writerows(registros)


def upload_blob(caminho_local: str, account: str, filesystem: str, blob_name: str):
    """Sobe um arquivo ao ADLS Gen2 via DefaultAzureCredential (sem chaves)."""
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient

    # No ADLS Gen2 (HNS), o filesystem é exposto como um container Blob;
    # o endpoint .blob.core.windows.net funciona para o OPENROWSET também.
    cred = DefaultAzureCredential()
    svc = BlobServiceClient(
        account_url=f"https://{account}.blob.core.windows.net",
        credential=cred,
    )
    client = svc.get_blob_client(container=filesystem, blob=blob_name)
    with open(caminho_local, "rb") as data:
        client.upload_blob(data, overwrite=True)
    print(f"  -> upload OK: {filesystem}/{blob_name}")


def main():
    parser = argparse.ArgumentParser(description="Gera logs de compras da QC (3 CSVs).")
    parser.add_argument("--out", default=".", help="Diretório de saída dos CSVs")
    parser.add_argument("--upload", action="store_true", help="Sobe os CSVs ao Lake (ADLS Gen2)")
    parser.add_argument("--account", help="Nome da conta ADLS Gen2 (output lake_account_name)")
    parser.add_argument("--filesystem", default="logs", help="Filesystem/container destino")
    parser.add_argument("--prefix", default="compras", help="Prefixo do blob (ex.: compras -> compras/...)")
    args = parser.parse_args()

    random.seed(SEED)
    os.makedirs(args.out, exist_ok=True)

    if args.upload and not args.account:
        parser.error("--upload exige --account <stqclakeXXXXXX>")

    total = 0
    pedido_inicial = 1
    for mes, sufixo in MESES:
        registros = gerar_registros(mes, REGISTROS_POR_ARQUIVO, pedido_inicial)
        pedido_inicial += REGISTROS_POR_ARQUIVO
        total += len(registros)

        nome = f"logs_compras_{sufixo}.csv"
        caminho = os.path.join(args.out, nome)
        escrever_csv(caminho, registros)
        tam = os.path.getsize(caminho)
        print(f"[OK] {nome}: {len(registros)} registros, {tam:,} bytes")

        if args.upload:
            # Sobe sob o prefixo compras/ para casar com o glob compras_*.csv
            blob_name = f"{args.prefix}_{sufixo}.csv"
            upload_blob(caminho, args.account, args.filesystem, blob_name)

    print(f"\nTotal: {total} registros em {len(MESES)} arquivos.")
    if not args.upload:
        print("Dica: rode com --upload --account <conta> para enviar ao Lake.")


if __name__ == "__main__":
    main()
