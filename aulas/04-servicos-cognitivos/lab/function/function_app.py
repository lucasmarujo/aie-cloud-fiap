"""
Function da Aula 4 — pipeline cognitivo da Quantum Commerce.

4 rotas HTTP, todas autenticadas via Managed Identity SystemAssigned:

    GET  /api/health              — status do serviço
    GET  /api/transcrever         — Speech-to-Text de áudio no Blob
    POST /api/analisar-reviews    — Language: sentimento + entidades das reviews do Cosmos
    GET  /api/analisar-imagem     — Vision: tags + OCR + caption de imagem no Blob

Sem chaves, senhas ou connection strings no código. Toda autenticação flui pela
identidade gerenciada do Function App, que tem 3 roles:
    - Cognitive Services User no AI Services
    - Storage Blob Data Reader no Storage da Aula 2
    - Cosmos DB Built-in Data Contributor no Cosmos da Aula 2

Variáveis de ambiente (configuradas pelo Terraform):
    AI_ENDPOINT             — endpoint do Azure AI Services
    STORAGE_ACCOUNT_AULA2   — nome do Storage Account da Aula 2
    COSMOS_ACCOUNT_AULA2    — nome da conta Cosmos DB da Aula 2
"""
import json
import logging
import os
import tempfile
import time

import azure.cognitiveservices.speech as speechsdk
import azure.functions as func
from azure.ai.textanalytics import TextAnalyticsClient
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

AI_ENDPOINT   = os.environ["AI_ENDPOINT"]
STORAGE_AULA2 = os.environ["STORAGE_ACCOUNT_AULA2"]
COSMOS_AULA2  = os.environ.get("COSMOS_ACCOUNT_AULA2")
AI_REGION     = os.environ.get("AI_REGION", "brazilsouth")

_credential = DefaultAzureCredential()
_blob_service = BlobServiceClient(
    f"https://{STORAGE_AULA2}.blob.core.windows.net",
    credential=_credential,
)


# ─────────────────────────────────────────────────────────────────────────────
# /health
# ─────────────────────────────────────────────────────────────────────────────
@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({
            "status": "ok",
            "service": "qc-cognitive",
            "rotas": ["/health", "/transcrever", "/analisar-reviews", "/analisar-imagem"],
        }),
        mimetype="application/json",
    )


# ─────────────────────────────────────────────────────────────────────────────
# /transcrever — Speech-to-Text
# ─────────────────────────────────────────────────────────────────────────────
@app.route(route="transcrever", methods=["GET", "POST"])
def transcrever(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/transcrever?blob=bbc-trecho.mp3&container=audios&idioma=pt-BR"""
    blob_name = req.params.get("blob", "bbc-trecho.mp3")
    container = req.params.get("container", "audios")
    idioma    = req.params.get("idioma", "pt-BR")

    logging.info(f"Transcrevendo {container}/{blob_name} em {idioma}")

    try:
        # 1. Baixar áudio do Blob via Managed Identity
        blob_client = _blob_service.get_blob_client(container=container, blob=blob_name)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(blob_client.download_blob().readall())
            audio_path = tmp.name

        # 2. Configurar Speech via token AAD (Managed Identity)
        token = _credential.get_token("https://cognitiveservices.azure.com/.default").token
        speech_config = speechsdk.SpeechConfig(auth_token=token, region=AI_REGION)
        speech_config.speech_recognition_language = idioma

        # 3. Reconhecimento contínuo (suporta áudios > 15s)
        audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, audio_config=audio_config
        )

        textos = []
        done = False

        def on_recognized(evt):
            textos.append(evt.result.text)

        def on_stopped(_evt):
            nonlocal done
            done = True

        recognizer.recognized.connect(on_recognized)
        recognizer.session_stopped.connect(on_stopped)
        recognizer.canceled.connect(on_stopped)

        recognizer.start_continuous_recognition()
        timeout = 60
        while not done and timeout > 0:
            time.sleep(1)
            timeout -= 1
        recognizer.stop_continuous_recognition()

        texto_completo = " ".join(textos).strip()
        os.unlink(audio_path)

        return func.HttpResponse(
            json.dumps(
                {"transcricao": texto_completo, "idioma": idioma},
                ensure_ascii=False,
            ),
            mimetype="application/json",
        )

    except Exception as e:
        logging.exception("Falha em /transcrever")
        return func.HttpResponse(
            json.dumps({"erro": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


# ─────────────────────────────────────────────────────────────────────────────
# /analisar-reviews — Language (sentimento + entidades)
# ─────────────────────────────────────────────────────────────────────────────
@app.route(route="analisar-reviews", methods=["GET", "POST"])
def analisar_reviews(req: func.HttpRequest) -> func.HttpResponse:
    """Lê reviews do Cosmos, analisa sentimento + entidades, atualiza Cosmos."""
    limit = int(req.params.get("limit", 10))
    logging.info(f"Analisando até {limit} reviews")

    try:
        # 1. Conectar no Cosmos via Managed Identity
        cosmos = CosmosClient(
            f"https://{COSMOS_AULA2}.documents.azure.com",
            credential=_credential,
        )
        container = cosmos.get_database_client("qc-db").get_container_client("reviews")

        # 2. Pegar reviews que ainda não foram processadas
        items = list(container.query_items(
            query=f"SELECT TOP {limit} * FROM c WHERE NOT IS_DEFINED(c.sentimento_label)",
            enable_cross_partition_query=True,
        ))

        if not items:
            return func.HttpResponse(
                json.dumps({"msg": "Nenhuma review nova para analisar"}),
                mimetype="application/json",
            )

        # 3. Language client via Managed Identity
        ta_client = TextAnalyticsClient(endpoint=AI_ENDPOINT, credential=_credential)

        documentos = [r["texto"] for r in items]

        # 4. Sentimento + entidades em batch (Language faz batch nativo)
        sentimentos = ta_client.analyze_sentiment(documentos, language="pt")
        entidades   = ta_client.recognize_entities(documentos, language="pt")

        # 5. Upsert cada review com novos campos
        resultados = []
        for i, item in enumerate(items):
            sent = sentimentos[i]
            ent  = entidades[i]

            if sent.is_error or ent.is_error:
                continue

            item["sentimento_label"] = sent.sentiment
            item["sentimento_score"] = {
                "positive": sent.confidence_scores.positive,
                "neutral":  sent.confidence_scores.neutral,
                "negative": sent.confidence_scores.negative,
            }
            item["entidades"] = [
                {"text": e.text, "category": e.category, "confidence": e.confidence_score}
                for e in ent.entities
            ]

            container.upsert_item(item)
            resultados.append({
                "id": item["id"],
                "sentimento": sent.sentiment,
                "entidades_count": len(item["entidades"]),
            })

        # 6. Resumo agregado
        positivos = sum(1 for r in resultados if r["sentimento"] == "positive")
        negativos = sum(1 for r in resultados if r["sentimento"] == "negative")

        return func.HttpResponse(
            json.dumps({
                "total_analisadas": len(resultados),
                "positivas": positivos,
                "negativas": negativos,
                "neutras":   len(resultados) - positivos - negativos,
                "exemplos":  resultados[:3],
            }, ensure_ascii=False),
            mimetype="application/json",
        )

    except Exception as e:
        logging.exception("Falha em /analisar-reviews")
        return func.HttpResponse(
            json.dumps({"erro": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


# ─────────────────────────────────────────────────────────────────────────────
# /analisar-imagem — Vision (tags + OCR + caption + objetos)
# ─────────────────────────────────────────────────────────────────────────────
@app.route(route="analisar-imagem", methods=["GET", "POST"])
def analisar_imagem(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/analisar-imagem?blob=cadeira.jpg&container=imagens"""
    blob_name = req.params.get("blob", "cadeira-produto.jpg")
    container = req.params.get("container", "imagens")

    logging.info(f"Analisando {container}/{blob_name}")

    try:
        # 1. Baixar imagem do Blob via Managed Identity
        blob_client = _blob_service.get_blob_client(container=container, blob=blob_name)
        image_data = blob_client.download_blob().readall()

        # 2. Vision client via Managed Identity
        vision_client = ImageAnalysisClient(endpoint=AI_ENDPOINT, credential=_credential)

        # 3. Análise multi-feature em uma única chamada
        result = vision_client.analyze(
            image_data=image_data,
            visual_features=[
                VisualFeatures.TAGS,
                VisualFeatures.CAPTION,
                VisualFeatures.READ,     # OCR
                VisualFeatures.OBJECTS,
            ],
            language="pt",
        )

        # 4. Estruturar resposta
        tags = [
            {"name": t.name, "confidence": round(t.confidence, 3)}
            for t in (result.tags.list if result.tags else [])
        ]
        caption = result.caption.text if result.caption else ""

        texto_extraido = ""
        if result.read:
            linhas = [line.text for block in result.read.blocks for line in block.lines]
            texto_extraido = "\n".join(linhas)

        objetos = [
            {"label": o.tags[0].name if o.tags else "obj", "box": list(o.bounding_box)}
            for o in (result.objects.list if result.objects else [])
        ]

        return func.HttpResponse(
            json.dumps({
                "caption": caption,
                "tags": tags[:10],
                "texto_extraido": texto_extraido,
                "objetos_detectados": objetos,
            }, ensure_ascii=False),
            mimetype="application/json",
        )

    except Exception as e:
        logging.exception("Falha em /analisar-imagem")
        return func.HttpResponse(
            json.dumps({"erro": str(e)}),
            mimetype="application/json",
            status_code=500,
        )
