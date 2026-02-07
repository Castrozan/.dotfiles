{
  openclaw = {
    userName = "Lucas";
    gatewayPort = 18789;
    agents = {
      clever = {
        enable = true;
        isDefault = true;
        emoji = "🤖";
        role = "home/personal — NixOS, home automation, overnight work";
        model.primary = "anthropic/claude-sonnet-4-5";
        workspace = "openclaw";
        tts.voice = "en-US-JennyNeural";
        telegram.enable = true;
      };
      golden = {
        enable = true;
        emoji = "🌟";
        role = "research & discovery — deep dives, analysis, long-form thinking";
        model.primary = "nvidia/moonshotai/kimi-k2.5";
        workspace = "openclaw/golden";
        tts.voice = "en-US-AriaNeural";
        telegram.enable = true;
      };
    };
  };
}
