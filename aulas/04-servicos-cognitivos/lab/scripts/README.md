# Scripts auxiliares — Aula 4

| Script | Quando usar |
|--------|-------------|
| [gerar_audio_tts.py](gerar_audio_tts.py) | **Fallback do L₂** se você não conseguir baixar um podcast público para testar `/transcrever`. Gera um áudio sintético em PT-BR usando o **mesmo recurso AI Services** do lab (TTS e STT moram juntos). |

## Como usar

Pré-requisito: Terraform da Aula 4 já aplicado, e `KEY_VAULT_NAME` + `AI_ENDPOINT` exportados:

```bash
cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/terraform
export AI_ENDPOINT=$(terraform output -raw ai_endpoint)
export KEY_VAULT_NAME=$(terraform output -raw key_vault_name)
```

Rodar:

```bash
pip install --user azure-cognitiveservices-speech azure-identity azure-keyvault-secrets

cd ~/aie-cloud/aulas/04-servicos-cognitivos/lab/scripts
python3 gerar_audio_tts.py
# Saída em ~/qc-aula04/audio-teste.wav
```

Depois, suba o arquivo para o container `audios` do Storage da Aula 2:

```bash
az storage blob upload \
  --account-name "$STORAGE_AULA2" \
  --container-name audios \
  --name audio-teste.wav \
  --file ~/qc-aula04/audio-teste.wav \
  --auth-mode login --overwrite
```

E teste a rota `/transcrever?blob=audio-teste.wav`.
