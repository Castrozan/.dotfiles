{ config, ... }:
let
  secretsDir = "${config.home.homeDirectory}/.config/voice-pipeline/secrets";
in
{
  services.voice-pipeline = {
    enable = true;
    gatewayUrl = "http://localhost:18789";
    gatewayTokenFile = "${secretsDir}/gateway-token";
    deepgramApiKeyFile = "${secretsDir}/deepgram-api-key";
    openaiApiKeyFile = "${secretsDir}/openai-api-key";
    defaultAgent = "jarvis";
    wakeWords = [
      "jarvis"
      "robson"
      "jenny"
    ];
    model = "openai-codex/gpt-5.3-codex";
    ttsEngine = "edge-tts";
    agents = {
      jarvis = {
        openaiVoice = "onyx";
        edgeTtsVoice = "en-GB-RyanNeural";
        language = "English";
      };
      robson = {
        openaiVoice = "echo";
        edgeTtsVoice = "pt-BR-AntonioNeural";
        language = "Portuguese";
      };
      jenny = {
        openaiVoice = "nova";
        edgeTtsVoice = "en-US-JennyNeural";
        language = "English";
      };
    };
  };
}
