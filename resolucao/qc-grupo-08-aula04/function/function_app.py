"""
function_app.py — Aula 4 — pipeline cognitivo da Quantum Commerce.

Rotas:
    GET  /api/health                        — status do serviço
    GET  /api/transcrever                   — Speech-to-Text de áudio no Blob
    POST /api/analisar-reviews              — pipeline robusto N2 2.1:
                                              PII redaction → resumo extractivo
                                              → opinion mining → upsert Cosmos
    GET  /api/analisar-imagem               — Vision: tags + OCR + caption
    GET  /api/sumarizar-reviews-produto     — LLM: síntese por produto (N3 3.3 — Pessoa 3)

Autenticação: Managed Identity SystemAssigned em toda saída de rede.
Roles necessárias na MI da Function:
    - Cognitive Services User               → AI Services (Language + Vision)
    - Cognitive Services OpenAI User        → Azure OpenAI (rota 3.3)
    - Storage Blob Data Reader              → Storage da Aula 2
    - Cosmos DB Built-in Data Contributor   → Cosmos da Aula 2

Variáveis de ambiente (injetadas pelo Terraform):
    AI_ENDPOINT             — endpoint do Azure AI Services
    STORAGE_ACCOUNT_AULA2   — nome do Storage Account da Aula 2
    COSMOS_ACCOUNT_AULA2    — nome da conta Cosmos DB da Aula 2
    AI_REGION               — região para o SDK de Speech (default: brazilsouth)
    AZURE_OPENAI_ENDPOINT   — endpoint do Azure OpenAI (necessário para 3.3)
    AZURE_OPENAI_DEPLOYMENT — nome do deployment gpt-4o-mini (necessário para 3.3)
"""
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timezone

import azure.cognitiveservices.speech as speechsdk
import azure.functions as func
from azure.ai.textanalytics import ExtractiveSummaryAction, TextAnalyticsClient
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.storage.blob import BlobServiceClient
from openai import AzureOpenAI

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

AI_ENDPOINT        = os.environ["AI_ENDPOINT"]
STORAGE_AULA2      = os.environ["STORAGE_ACCOUNT_AULA2"]
COSMOS_AULA2       = os.environ.get("COSMOS_ACCOUNT_AULA2")
AI_REGION          = os.environ.get("AI_REGION", "brazilsouth")
OPENAI_ENDPOINT    = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
OPENAI_DEPLOYMENT  = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

_credential = DefaultAzureCredential()
_blob_service = BlobServiceClient(
    f"https://{STORAGE_AULA2}.blob.core.windows.net",
    credential=_credential,
)

# Cliente OpenAI com token AAD via MI — usado pela rota 3.3 (Pessoa 3)
_token_provider = get_bearer_token_provider(
    _credential, "https://cognitiveservices.azure.com/.default"
)
_openai = AzureOpenAI(
    azure_endpoint=OPENAI_ENDPOINT,
    azure_ad_token_provider=_token_provider,
    api_version="2024-10-21",
) if OPENAI_ENDPOINT else None


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────
def _json_response(body: dict, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(body, ensure_ascii=False),
        mimetype="application/json",
        status_code=status_code,
    )


# ─────────────────────────────────────────────────────────────────────────────
# /health
# ─────────────────────────────────────────────────────────────────────────────
@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return _json_response({
        "status": "ok",
        "service": "qc-cognitive",
        "rotas": [
            "/health",
            "/transcrever",
            "/analisar-reviews",
            "/analisar-imagem",
            "/sumarizar-reviews-produto",
        ],
    })


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
        blob_client = _blob_service.get_blob_client(container=container, blob=blob_name)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(blob_client.download_blob().readall())
            audio_path = tmp.name

        token = _credential.get_token("https://cognitiveservices.azure.com/.default").token
        speech_config = speechsdk.SpeechConfig(auth_token=token, region=AI_REGION)
        speech_config.speech_recognition_language = idioma

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

        return _json_response({"transcricao": texto_completo, "idioma": idioma})

    except Exception as e:
        logging.exception("Falha em /transcrever")
        return _json_response({"erro": str(e)}, 500)


# ─────────────────────────────────────────────────────────────────────────────
# /analisar-reviews — N2 2.1: pipeline robusto
# ─────────────────────────────────────────────────────────────────────────────
@app.route(route="analisar-reviews", methods=["GET", "POST"])
def analisar_reviews(req: func.HttpRequest) -> func.HttpResponse:
    """
    Pipeline N2 2.1 em 4 passos sobre cada review:
      1. PII redaction (LGPD — roda antes de qualquer persistência)
      2. Opinion mining (sentimento + aspectos)
      3. Entity recognition
      4. Extractive summarization (reviews > 300 chars)
    Upsert no Cosmos com schema completo.
    """
    limit = int(req.params.get("limit", 10))
    logging.info(f"Pipeline 2.1: processando até {limit} reviews")

    try:
        cosmos = CosmosClient(
            f"https://{COSMOS_AULA2}.documents.azure.com",
            credential=_credential,
        )
        reviews_ctr = (
            cosmos
            .get_database_client("qc-db")
            .get_container_client("reviews")
        )

        items = list(reviews_ctr.query_items(
            query=f"SELECT TOP {limit} * FROM c WHERE NOT IS_DEFINED(c.texto_redacted)",
            enable_cross_partition_query=True,
        ))

        if not items:
            return _json_response({"msg": "Nenhuma review nova para processar"})

        ta = TextAnalyticsClient(endpoint=AI_ENDPOINT, credential=_credential)
        textos = [item["texto"] for item in items]

        # ── Passo 1: PII redaction ────────────────────────────────────────────
        # Obrigatório rodar primeiro: o texto_redacted alimenta todos os passos
        # seguintes e é o único que pode ser persistido sem violar a LGPD.
        pii_results = ta.recognize_pii_entities(textos, language="pt")
        textos_redacted = [
            "" if r.is_error else r.redacted_text
            for r in pii_results
        ]

        # ── Passo 2: Opinion Mining (sentimento + aspectos) ───────────────────
        sent_results = ta.analyze_sentiment(
            textos_redacted, language="pt", show_opinion_mining=True
        )

        # ── Passo 3: Reconhecimento de entidades ──────────────────────────────
        ent_results = ta.recognize_entities(textos_redacted, language="pt")

        # ── Passo 4: Summarization extractiva (só para reviews longas) ────────
        resumos = [""] * len(items)
        idx_longos = [i for i, t in enumerate(textos) if len(t) > 300]

        if idx_longos:
            docs_longos = [textos_redacted[i] for i in idx_longos]
            poller = ta.begin_analyze_actions(
                docs_longos,
                actions=[ExtractiveSummaryAction(max_sentence_count=1)],
                language="pt",
            )
            # flatten pages → um item por documento
            summ_results = [doc for page in poller.result() for doc in page]
            for j, doc_result in enumerate(summ_results):
                for summ in doc_result.extractive_summary_results:
                    if not summ.is_error and summ.sentences:
                        resumos[idx_longos[j]] = summ.sentences[0].text

        # ── Upsert no Cosmos com schema completo do Ex. 2.1 ──────────────────
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        processados = []

        for i, item in enumerate(items):
            sent = sent_results[i]
            ent  = ent_results[i]
            if sent.is_error or ent.is_error:
                logging.warning(f"Erro em review {item.get('id')}: sent={sent.is_error} ent={ent.is_error}")
                continue

            # opinion mining: target (aspecto) → sentimento da avaliação
            aspectos = []
            for sentence in sent.sentences:
                for mined_opinion in sentence.mined_opinions:
                    aspectos.append({
                        "texto":     mined_opinion.target.text,
                        "sentimento": mined_opinion.target.sentiment,
                    })

            item.update({
                "texto_redacted":   textos_redacted[i],
                "sentimento_label": sent.sentiment,
                "sentimento_score": {
                    "positive": round(sent.confidence_scores.positive, 3),
                    "neutral":  round(sent.confidence_scores.neutral,  3),
                    "negative": round(sent.confidence_scores.negative, 3),
                },
                "aspectos": aspectos,
                "entidades": [
                    {
                        "text":       e.text,
                        "category":   e.category,
                        "confidence": round(e.confidence_score, 3),
                    }
                    for e in ent.entities
                ],
                "resumo":        resumos[i],
                "processado_em": ts,
            })
            reviews_ctr.upsert_item(item)
            processados.append({
                "id":             item["id"],
                "sentimento":     sent.sentiment,
                "aspectos_count": len(aspectos),
                "tem_resumo":     bool(resumos[i]),
            })

        pos = sum(1 for r in processados if r["sentimento"] == "positive")
        neg = sum(1 for r in processados if r["sentimento"] == "negative")
        return _json_response({
            "total_processadas": len(processados),
            "positivas":  pos,
            "negativas":  neg,
            "neutras":    sum(1 for r in processados if r["sentimento"] == "neutral"),
            "mistas":     sum(1 for r in processados if r["sentimento"] == "mixed"),
            "exemplos":   processados[:3],
        })

    except Exception as e:
        logging.exception("Falha em /analisar-reviews")
        return _json_response({"erro": str(e)}, 500)


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
        blob_client = _blob_service.get_blob_client(container=container, blob=blob_name)
        image_data = blob_client.download_blob().readall()

        vision_client = ImageAnalysisClient(endpoint=AI_ENDPOINT, credential=_credential)
        result = vision_client.analyze(
            image_data=image_data,
            visual_features=[
                VisualFeatures.TAGS,
                VisualFeatures.CAPTION,
                VisualFeatures.READ,
                VisualFeatures.OBJECTS,
            ],
            language="pt",
        )

        tags = [
            {"name": t.name, "confidence": round(t.confidence, 3)}
            for t in (result.tags.list if result.tags else [])
        ]
        caption = result.caption.text if result.caption else ""
        texto_extraido = ""
        if result.read:
            texto_extraido = "\n".join(
                line.text
                for block in result.read.blocks
                for line in block.lines
            )
        objetos = [
            {"label": o.tags[0].name if o.tags else "obj", "box": list(o.bounding_box)}
            for o in (result.objects.list if result.objects else [])
        ]

        return _json_response({
            "caption":           caption,
            "tags":              tags[:10],
            "texto_extraido":    texto_extraido,
            "objetos_detectados": objetos,
        })

    except Exception as e:
        logging.exception("Falha em /analisar-imagem")
        return _json_response({"erro": str(e)}, 500)


# ─────────────────────────────────────────────────────────────────────────────
# /sumarizar-reviews-produto — N3 3.3 (Pessoa 3 — Lucas Marujo)
# ─────────────────────────────────────────────────────────────────────────────
COSMOS_DB             = os.environ.get("COSMOS_DB", "qc-db")
COSMOS_CTR_REVIEWS    = os.environ.get("COSMOS_CONTAINER_REVIEWS", "reviews")

_cosmos_client = CosmosClient(
    f"https://{COSMOS_AULA2}.documents.azure.com",
    credential=_credential,
) if COSMOS_AULA2 else None

SYSTEM_PROMPT_SUMM = (
    "Você é um analista de e-commerce da Quantum Commerce. Analise as reviews do "
    "produto e responda SOMENTE com um JSON válido no formato:\n"
    '{\n'
    '  "resumo_geral": "1-2 frases",\n'
    '  "pontos_positivos": ["..."],\n'
    '  "pontos_negativos": ["..."],\n'
    '  "recomendacoes_de_acao": ["..."]\n'
    "}\n"
    "Baseie-se apenas nas reviews fornecidas. Não invente fatos. "
    "Priorize os aspectos mais recorrentes."
)


def _ler_reviews_produto(produto_id: str) -> list[dict]:
    ctr = _cosmos_client.get_database_client(COSMOS_DB).get_container_client(COSMOS_CTR_REVIEWS)
    return list(ctr.query_items(
        query="SELECT r.texto_redacted, r.sentimento_label, r.aspectos FROM r WHERE r.produto_id = @pid",
        parameters=[{"name": "@pid", "value": produto_id}],
        enable_cross_partition_query=True,
    ))


def _montar_reviews_texto(reviews: list[dict]) -> str:
    linhas = []
    for r in reviews:
        aspectos = ", ".join(
            f'{a["texto"]}:{a["sentimento"]}' for a in r.get("aspectos", [])
        )
        linhas.append(
            f'- ({r.get("sentimento_label", "n/a")}) {r.get("texto_redacted", "")}'
            + (f" [aspectos: {aspectos}]" if aspectos else "")
        )
    return "\n".join(linhas)


@app.route(route="sumarizar-reviews-produto", methods=["GET"])
def sumarizar_reviews_produto(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/sumarizar-reviews-produto?produto_id=5 — N3 3.3."""
    produto_id = (req.params.get("produto_id") or "").strip()
    if not produto_id:
        return _json_response({"erro": "produto_id é obrigatório"}, 400)
    if not _openai:
        return _json_response({"erro": "AZURE_OPENAI_ENDPOINT não configurado"}, 503)

    try:
        reviews = _ler_reviews_produto(produto_id)
    except Exception as e:
        logging.exception("Falha ao ler reviews do Cosmos")
        return _json_response({"erro": f"falha ao acessar cosmos: {e!s}"}, 500)

    if not reviews:
        return _json_response({"erro": "produto sem reviews"}, 404)

    user_prompt = f"Produto: {produto_id}\n\nReviews:\n{_montar_reviews_texto(reviews)}"
    try:
        completion = _openai.chat.completions.create(
            model=OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_SUMM},
                {"role": "user",   "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        analise = json.loads(completion.choices[0].message.content)
    except Exception as e:
        logging.exception("Falha na chamada ao Azure OpenAI")
        return _json_response({"erro": f"falha no llm: {e!s}"}, 502)

    return _json_response({
        "produto_id":    produto_id,
        "total_reviews": len(reviews),
        "analise":       analise,
    })
