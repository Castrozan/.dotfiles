{
  openclaw.mesh = {
    connections.sshHost = "100.127.240.60";
    connections.sshUser = "lucas.zanoni";
    gridAgents = [
      {
        id = "robson";
        emoji = "⚽";
        model = "sonnet-4.5";
      }
      {
        id = "jenny";
        emoji = "🎀";
        model = "kimi-k2.5";
      }
      {
        id = "monster";
        emoji = "👾";
        model = "kimi-k2.5";
      }
      {
        id = "silver";
        emoji = "🪙";
        model = "kimi-k2.5";
      }
    ];
  };

  openclaw = {
    userName = "Lucas";
    gatewayPort = 18790;
    agents = {
      robson = {
        enable = true;
        isDefault = true;
        emoji = "⚽";
        role = "work — Betha, code, productivity";
        model.primary = "anthropic/claude-sonnet-4-5";
        workspace = "openclaw/robson";
        tts.voice = "pt-BR-AntonioNeural";
        telegram.enable = true;
      };
      jenny = {
        enable = true;
        emoji = "🎀";
        role = "personal assistant, reminders, scheduling";
        model.primary = "nvidia/moonshotai/kimi-k2.5";
        workspace = "openclaw/jenny";
        tts.voice = "en-US-JennyNeural";
        telegram.enable = true;
      };
      monster = {
        enable = true;
        emoji = "👾";
        role = "creative assistant, brainstorming, fun tasks";
        model.primary = "nvidia/moonshotai/kimi-k2.5";
        workspace = "openclaw/monster";
        tts.voice = "en-US-GuyNeural";
        telegram.enable = true;
      };
      silver = {
        enable = true;
        emoji = "🪙";
        role = "research & analysis — technical deep dives, documentation, investigation";
        model.primary = "nvidia/moonshotai/kimi-k2.5";
        workspace = "openclaw/silver";
        tts.voice = "pt-BR-FranciscaNeural";
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
