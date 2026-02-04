{
  openclaw = {
    userName = "Lucas";
    gatewayPort = 18790;
    agents = {
      robson = {
        enable = true;
        isDefault = true;
        emoji = "⚽";
        role = "work — Betha, code, productivity";
        model.primary = "nvidia/moonshotai/kimi-k2.5";
        workspace = "openclaw/robson";
        tts.voice = "pt-BR-AntonioNeural";
        telegram.enable = true;
      };
      jenny = {
        enable = true;
        emoji = "🎀";
        role = "personal assistant, reminders, scheduling";
        model.primary = "anthropic/claude-sonnet-4-5";
        workspace = "openclaw/jenny";
        tts.voice = "en-US-JennyNeural";
        telegram.enable = true;
      };
    };
  };
}
