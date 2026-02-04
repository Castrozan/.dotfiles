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
        model.primary = "nvidia/moonshotai/kimi-k2.5";
        workspace = "openclaw";
        tts.voice = "en-US-JennyNeural";
        telegram.enable = true;
      };
    };
  };
}
