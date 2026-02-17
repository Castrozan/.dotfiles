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
    wakeWordAlternatives = {
      jarvis = [
        "jarvus"
        "jarves"
        "jervis"
        "gervis"
        "jarvas"
      ];
      robson = [
        "rabson"
        "robsen"
        "robeson"
        "robs"
        "robsun"
        "rabs"
        "robinson"
        "robzon"
      ];
      jenny = [
        "jeni"
        "jeny"
        "jenni"
        "jennie"
        "genie"
      ];
    };
    model = "anthropic/claude-sonnet-4-5";
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
