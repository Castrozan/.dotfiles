{
  services.hey-bot = {
    enable = true;
    keywords = [
      "robson"
      "robinson"
      "robeson"
      "robzon"
      "jenny"
      "jeni"
      "jennie"
      "genie"
      "monster"
      "monstro"
      "munster"
      "silver"
      "silva"
      "sylver"
      "silber"
      "jarvis"
      "jarves"
      "jarvus"
      "jervis"
    ];
    gatewayUrl = "http://localhost:18790";
    agentId = "main";
    ttsVoice = "pt-BR-AntonioNeural";
    model = "anthropic/claude-sonnet-4-5";
  };
}
