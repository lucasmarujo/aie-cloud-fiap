"""
Script auxiliar — gera um áudio sintético em PT-BR usando Azure TTS.

Útil como fallback se você não conseguir baixar um podcast/áudio público
para testar a rota /transcrever no L₂. Use o MESMO recurso Azure AI
Services do lab — tanto TTS quanto STT moram nele.

Variáveis de ambiente necessárias:
    AI_ENDPOINT      — endpoint do Azure AI Services
    KEY_VAULT_NAME   — nome do Key Vault (com o segredo ai-services-key)
    AI_REGION        — região (default: brazilsouth)

Saída: ~/qc-aula04/audio-teste.wav

Dependências:
    pip install --user azure-cognitiveservices-speech azure-identity azure-keyvault-secrets
"""
import os
import sys

import azure.cognitiveservices.speech as speechsdk
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

TEXTO = """
A Quantum Commerce é uma plataforma de e-commerce que opera em doze países.
Nossos agentes de inteligência artificial ajudam clientes a encontrar produtos,
calcular fretes, processar pedidos e responder dúvidas em tempo real.
"""

VOZ = "pt-BR-AntonioNeural"  # outras opções: pt-BR-FranciscaNeural, pt-BR-ThalitaNeural
SAIDA = os.path.expanduser("~/qc-aula04/audio-teste.wav")


def main():
    kv_name = os.environ["KEY_VAULT_NAME"]
    region  = os.environ.get("AI_REGION", "brazilsouth")

    # 1. Ler chave do AI Services do Key Vault (usando MI do Cloud Shell)
    cred = DefaultAzureCredential()
    kv_client = SecretClient(f"https://{kv_name}.vault.azure.net", credential=cred)
    ai_key = kv_client.get_secret("ai-services-key").value
    print(f"✓ Chave do AI Services lida de {kv_name}")

    # 2. Configurar TTS
    speech_config = speechsdk.SpeechConfig(subscription=ai_key, region=region)
    speech_config.speech_synthesis_voice_name = VOZ

    # Garantir que a pasta de saída exista
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=SAIDA)

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=audio_config
    )

    # 3. Sintetizar
    print(f"→ Sintetizando áudio com voz '{VOZ}'...")
    result = synthesizer.speak_text_async(TEXTO).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"✓ Áudio salvo em {SAIDA}")
        print(f"  Tamanho: {os.path.getsize(SAIDA)} bytes")
    else:
        print(f"✗ Erro na síntese: {result.reason}")
        if result.reason == speechsdk.ResultReason.Canceled:
            details = speechsdk.CancellationDetails(result)
            print(f"  Detalhe: {details.reason} — {details.error_details}")
        sys.exit(1)


if __name__ == "__main__":
    main()
