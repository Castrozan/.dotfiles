{ config, ... }:
let
  agenixSecretsDir = "${config.home.homeDirectory}/.secrets";
in
{
  systemd.user.services.voice-pipeline.Service.Environment = [
    "VOICE_PIPELINE_COMPLETION_ENGINE=cli"
    "VOICE_PIPELINE_COMPLETION_CLI_COMMAND=claude -p"
  ];

  services.voice-pipeline = {
    enable = true;
    gatewayUrl = "http://localhost:18789";
    gatewayTokenFile = "${agenixSecretsDir}/voice-pipeline-gateway-token";
    deepgramApiKeyFile = "${agenixSecretsDir}/deepgram-api-key";
    openaiApiKeyFile = "${agenixSecretsDir}/openai-api-key";
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
