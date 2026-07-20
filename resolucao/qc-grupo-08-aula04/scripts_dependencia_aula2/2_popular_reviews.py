"""
Passo 2 — Insere 30 reviews fictícias no Cosmos DB (container 'reviews').

Fonte: Aula 2 / Atividade 3-A (script original preservado sem alterações).

Variáveis de ambiente:
    COSMOS_ENDPOINT  — terraform output -raw cosmos_endpoint (Aula 2)

Dependências:
    pip install --user azure-identity azure-cosmos
"""

import os
import random

from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

TEMPLATES = [
    ("Adorei! Chegou rápido e funcionou perfeitamente.", 5),
    ("Produto excelente, recomendo demais.", 5),
    ("Cumpre o que promete, vale a pena pelo preço.", 4),
    ("Bom produto, mas a embalagem chegou amassada.", 4),
    ("Funciona ok, nada de especial.", 3),
    ("Esperava mais pelo valor pago.", 2),
    ("Decepcionante, não recomendo.", 1),
    ("Veio com defeito, tive que trocar.", 1),
    ("Maravilhoso, superou expectativas!", 5),
    ("Compraria de novo, ótimo custo-benefício.", 5),
    # Reviews mais longas (>300 chars) para testar o summarization do N2 2.1
    (
        "Comprei este produto há três semanas e posso dizer que superou minhas expectativas em todos os aspectos. "
        "A qualidade do material é superior ao que aparece nas fotos do site, e o acabamento é impecável. "
        "A entrega foi rápida, chegou em apenas dois dias úteis, bem embalado e sem nenhum dano. "
        "O atendimento da loja também foi excelente — respondi uma dúvida em menos de 1 hora. "
        "Só tenho elogios, com certeza voltarei a comprar.",
        5,
    ),
    (
        "Produto com boa qualidade, mas tive problemas sérios com o processo de entrega. "
        "O prazo informado no site era de 5 dias úteis, porém o produto levou 12 dias para chegar. "
        "Tentei contato pelo chat três vezes e não obtive resposta satisfatória — os atendentes repetiam "
        "as mesmas informações genéricas sem conseguir resolver o problema. "
        "Quando o produto finalmente chegou, estava em perfeitas condições, o que amenizou a frustração. "
        "Nota 3: produto ótimo, logística e atendimento precisam melhorar muito.",
        3,
    ),
]


def main():
    endpoint   = os.environ["COSMOS_ENDPOINT"]
    credential = DefaultAzureCredential()

    client    = CosmosClient(endpoint, credential=credential)
    db        = client.get_database_client("qc-db")
    container = db.get_container_client("reviews")

    print(f"→ Inserindo reviews em {endpoint}...")

    random.seed(42)
    inseridos = 0
    for i in range(1, 31):
        produto_id = random.randint(1, 20)
        texto, score = random.choice(TEMPLATES)
        review = {
            "id":         f"r-{i:03d}",
            "produto_id": str(produto_id),
            "score":      score,
            "texto":      texto,
            "cliente":    f"cliente-{random.randint(100, 999)}",
        }
        container.upsert_item(review)
        inseridos += 1

    print(f"✓ {inseridos} reviews inseridas")

    print("\n=== Reviews 4+ do produto 5 (verificação) ===")
    items = list(container.query_items(
        query="SELECT * FROM c WHERE c.produto_id = @pid AND c.score >= 4",
        parameters=[{"name": "@pid", "value": "5"}],
        enable_cross_partition_query=False,
    ))
    for r in items:
        print(f"  [score {r['score']}] {r['texto'][:80]}...")

    print("\nPróximo passo: python 3_indexar_produtos.py")


if __name__ == "__main__":
    main()
