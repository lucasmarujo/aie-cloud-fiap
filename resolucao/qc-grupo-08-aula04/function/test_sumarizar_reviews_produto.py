"""
Teste offline da rota N3 3.3 `/sumarizar-reviews-produto` (Pessoa 3 — Lucas).

Valida a lógica da rota sem tocar no Azure: faz stub dos SDKs Azure em
sys.modules, importa o `function_app.py` real e exercita o handler com
Cosmos e Azure OpenAI mockados.

Rodar (não precisa dos pacotes azure-*, só stdlib):
    python test_sumarizar_reviews_produto.py
"""
import json
import sys
import types


# ── Stubs dos SDKs Azure (não instalados no ambiente de teste) ───────────────
def _stub_azure_modules():
    def mod(name):
        m = types.ModuleType(name)
        sys.modules[name] = m
        return m

    class _AuthLevel:
        ANONYMOUS = "anonymous"

    class _FunctionApp:
        def __init__(self, *a, **k):
            pass

        def route(self, *a, **k):
            return lambda fn: fn  # decorator no-op: devolve a função intacta

    class _HttpRequest:
        def __init__(self, params=None):
            self.params = params or {}

    class _HttpResponse:
        def __init__(self, body, mimetype=None, status_code=200):
            self.body = body
            self.mimetype = mimetype
            self.status_code = status_code

    func = mod("azure.functions")
    func.FunctionApp = _FunctionApp
    func.AuthLevel = _AuthLevel
    func.HttpRequest = _HttpRequest
    func.HttpResponse = _HttpResponse

    speech = mod("azure.cognitiveservices.speech")
    speech.SpeechConfig = speech.SpeechRecognizer = object
    speech.audio = types.SimpleNamespace(AudioConfig=object)

    ta = mod("azure.ai.textanalytics")
    ta.TextAnalyticsClient = ta.ExtractiveSummaryAction = object

    vision = mod("azure.ai.vision.imageanalysis")
    vision.ImageAnalysisClient = object
    vmodels = mod("azure.ai.vision.imageanalysis.models")
    vmodels.VisualFeatures = object

    cosmos = mod("azure.cosmos")
    cosmos.CosmosClient = lambda *a, **k: object()

    identity = mod("azure.identity")
    identity.DefaultAzureCredential = lambda *a, **k: object()
    identity.get_bearer_token_provider = lambda *a, **k: (lambda: "token")

    blob = mod("azure.storage.blob")
    blob.BlobServiceClient = lambda *a, **k: object()

    openai = mod("openai")
    openai.AzureOpenAI = lambda *a, **k: object()

    # pacotes-pai precisam existir para o import funcionar
    for parent in ("azure", "azure.ai", "azure.ai.vision", "azure.cognitiveservices"):
        sys.modules.setdefault(parent, types.ModuleType(parent))


def _import_function_app():
    import os

    os.environ.setdefault("AI_ENDPOINT", "https://fake.cognitiveservices.azure.com/")
    os.environ.setdefault("STORAGE_ACCOUNT_AULA2", "fakestorage")
    os.environ.setdefault("COSMOS_ACCOUNT_AULA2", "fakecosmos")
    os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://fake.openai.azure.com/")
    _stub_azure_modules()
    import function_app
    return function_app


# ── Fakes de comportamento (Cosmos + OpenAI) ─────────────────────────────────
class _FakeCompletion:
    def __init__(self, content):
        msg = types.SimpleNamespace(content=content)
        self.choices = [types.SimpleNamespace(message=msg)]


class _FakeOpenAI:
    def __init__(self, content):
        self._content = content
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        self.last_kwargs = kwargs
        return _FakeCompletion(self._content)


REVIEWS_FAKE = [
    {"texto_redacted": "Ótimo produto", "sentimento_label": "positive",
     "aspectos": [{"texto": "qualidade", "sentimento": "positive"}]},
    {"texto_redacted": "Entrega atrasou", "sentimento_label": "negative",
     "aspectos": [{"texto": "entrega", "sentimento": "negative"}]},
]

ANALISE_FAKE = {
    "resumo_geral": "Produto bem avaliado, mas com atraso na entrega.",
    "pontos_positivos": ["qualidade"],
    "pontos_negativos": ["entrega atrasada"],
    "recomendacoes_de_acao": ["Revisar SLA da transportadora"],
}


def run():
    fa = _import_function_app()
    func = sys.modules["azure.functions"]

    # 1) _montar_reviews_texto: formata cada review com label + aspectos
    texto = fa._montar_reviews_texto(REVIEWS_FAKE)
    assert "(positive) Ótimo produto [aspectos: qualidade:positive]" in texto
    assert "(negative) Entrega atrasou [aspectos: entrega:negative]" in texto

    # 2) produto_id ausente → 400
    resp = fa.sumarizar_reviews_produto(func.HttpRequest(params={}))
    assert resp.status_code == 400, resp.status_code
    assert "produto_id" in json.loads(resp.body)["erro"]

    # 3) OpenAI não configurado → 503
    _openai_bkp = fa._openai
    fa._openai = None
    resp = fa.sumarizar_reviews_produto(func.HttpRequest(params={"produto_id": "5"}))
    assert resp.status_code == 503, resp.status_code
    fa._openai = _openai_bkp

    # 4) produto sem reviews → 404
    fa._openai = _FakeOpenAI(json.dumps(ANALISE_FAKE))
    fa._ler_reviews_produto = lambda pid: []
    resp = fa.sumarizar_reviews_produto(func.HttpRequest(params={"produto_id": "999"}))
    assert resp.status_code == 404, resp.status_code

    # 5) caminho feliz → 200 com análise parseada do LLM
    fa._ler_reviews_produto = lambda pid: REVIEWS_FAKE
    resp = fa.sumarizar_reviews_produto(func.HttpRequest(params={"produto_id": "5"}))
    assert resp.status_code == 200, resp.status_code
    body = json.loads(resp.body)
    assert body["produto_id"] == "5"
    assert body["total_reviews"] == 2
    assert body["analise"] == ANALISE_FAKE
    # o LLM foi chamado exigindo JSON e com temperatura baixa (síntese factual)
    kwargs = fa._openai.last_kwargs
    assert kwargs["response_format"] == {"type": "json_object"}
    assert kwargs["temperature"] == 0.2

    # 6) LLM devolve JSON inválido → 502
    fa._openai = _FakeOpenAI("isto não é json")
    resp = fa.sumarizar_reviews_produto(func.HttpRequest(params={"produto_id": "5"}))
    assert resp.status_code == 502, resp.status_code

    print("OK — 6 cenários da rota /sumarizar-reviews-produto passaram")


if __name__ == "__main__":
    run()
