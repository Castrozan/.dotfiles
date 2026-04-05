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
      "jarvis"
      "jarves"
      "jarvus"
      "jervis"
    ];
    gatewayUrl = "http://localhost:18789";
    agentId = "main";
    ttsVoice = "en-US-JennyNeural";
    model = "openai-codex/gpt-5.3-codex";
  };
}
