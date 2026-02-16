{ config, ... }:
let
  secretsDir = "${config.home.homeDirectory}/.openclaw/secrets";
in
{
  services.voice-pipeline = {
    enable = true;
    gatewayUrl = "http://localhost:${toString config.openclaw.gatewayPort}";
    gatewayTokenFile = "${secretsDir}/openclaw-gateway-token";
    deepgramApiKeyFile = "${secretsDir}/deepgram-api-key";
    openaiApiKeyFile = "${secretsDir}/openai-api-key";
    defaultAgent = "jarvis";
    wakeWords = [
      "jarvis"
      "robson"
      "jenny"
    ];
    model = "anthropic/claude-sonnet-4-5";
    ttsEngine = "edge-tts";
    agents = {
      jarvis = {
        openaiVoice = "onyx";
        edgeTtsVoice = "en-GB-RyanNeural";
      };
      robson = {
        openaiVoice = "echo";
        edgeTtsVoice = "pt-BR-AntonioNeural";
      };
      jenny = {
        openaiVoice = "nova";
        edgeTtsVoice = "en-US-JennyNeural";
      };
    };
  };
}
