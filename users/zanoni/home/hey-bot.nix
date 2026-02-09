{
  services.hey-bot = {
    enable = true;
    keywords = [
      "clever"
      "klever"
      "cleaver"
      "clover"
      "clebert"
      "kleiber"
      "klebber"
      "cleyber"
      "golden"
      "goulden"
    ];
    gatewayUrl = "http://localhost:18789";
    agentId = "main";
    ttsVoice = "en-US-JennyNeural";
    model = "anthropic/claude-sonnet-4-5";
  };
}
