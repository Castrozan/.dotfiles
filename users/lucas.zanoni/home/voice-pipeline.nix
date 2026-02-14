{ config, ... }:
{
  services.voice-pipeline = {
    enable = true;
    gatewayUrl = "http://localhost:${toString config.openclaw.gatewayPort}";
    defaultAgent = "jarvis";
    wakeWords = [
      "jarvis"
      "clever"
      "golden"
    ];
    model = "anthropic/claude-sonnet-4-5";
    agents = {
      jarvis.openaiVoice = "onyx";
      clever.openaiVoice = "nova";
      golden.openaiVoice = "echo";
    };
  };
}
