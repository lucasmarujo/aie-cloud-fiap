"""
Aula 5 / Atividade 3 — Versão job-friendly do treino.

Recebe inputs como argumentos CLI (em vez de env vars do shell). É a versão
executada pelo Compute Cluster quando o job é submetido via `job.yml`.

MLflow tracking é automático em jobs do Azure ML — o tracking URI já vem
configurado pelo runtime do Workspace, não precisamos chamar
`set_tracking_uri()`.

Argumentos:
    --input-data       — caminho local do produtos.csv (montado pelo job)
    --n-neighbors      — número de vizinhos (default: 5)
    --embedding-model  — modelo de embedding (default: all-MiniLM-L6-v2)
"""
import argparse
import os
import pickle

import mlflow
import mlflow.sklearn
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-data",
        type=str,
        required=True,
        help="Caminho do produtos.csv (montado pelo job a partir do Data Asset)",
    )
    parser.add_argument("--n-neighbors", type=int, default=5)
    parser.add_argument(
        "--embedding-model", type=str, default="all-MiniLM-L6-v2"
    )
    args = parser.parse_args()

    # Log de params
    mlflow.log_param("n_neighbors", args.n_neighbors)
    mlflow.log_param("embedding_model", args.embedding_model)
    mlflow.log_param("metric", "cosine")

    # Carregar dataset
    print(f"→ Carregando dataset de {args.input_data}")
    df = pd.read_csv(args.input_data)
    mlflow.log_metric("num_produtos", len(df))

    # Embeddings
    print(f"→ Gerando embeddings com {args.embedding_model}")
    model_emb = SentenceTransformer(args.embedding_model)
    textos = (df["nome"] + ". " + df["descricao"]).tolist()
    embeddings = model_emb.encode(textos, show_progress_bar=False)
    mlflow.log_metric("embedding_dim", embeddings.shape[1])

    # Treino
    print(f"→ Treinando NearestNeighbors n={args.n_neighbors}")
    nn = NearestNeighbors(n_neighbors=args.n_neighbors + 1, metric="cosine")
    nn.fit(embeddings)

    # Precision proxy
    _, indices = nn.kneighbors(embeddings)
    same_cat = sum(
        1
        for i, viz in enumerate(indices)
        for j in viz[1:]
        if df.iloc[j]["categoria"] == df.iloc[i]["categoria"]
    )
    total = len(df) * args.n_neighbors
    precision = same_cat / total
    mlflow.log_metric("precision_at_k_proxy", precision)
    print(f"✓ Precision proxy: {precision:.3f}")

    # Salvar artefato no output do job
    os.makedirs("./outputs", exist_ok=True)
    with open("./outputs/nn_model.pkl", "wb") as f:
        pickle.dump({"nn": nn, "embeddings": embeddings, "df": df}, f)

    # Registrar no Model Registry
    mlflow.sklearn.log_model(
        nn,
        "model",
        registered_model_name="recomendador-qc",
    )
    print("✓ Modelo registrado no Registry")


if __name__ == "__main__":
    main()
