{
  openclaw = {
    memorySync = {
      enable = true;
      remoteHost = "dellg15";
      remoteUser = "zanoni";
    };

    mesh = {
      connections.sshHost = "100.127.240.60";
      connections.sshUser = "lucas.zanoni";
      gridAgents = [
        {
          id = "robson";
          emoji = "⚽";
          model = "opus-4.6";
        }
        {
          id = "jenny";
          emoji = "🎀";
          model = "opus-4.6";
        }
        {
          id = "monster";
          emoji = "👾";
          model = "opus-4.6";
        }
        {
          id = "silver";
          emoji = "🪙";
          model = "sonnet-4.6";
        }
      ];
    };

    userName = "Lucas";
    gatewayPort = 18790;
    gatewayService.enable = true;
    coreRulesContent = builtins.readFile ../../../agents/core.md;
    agents = {
      robson = {
        enable = true;
        isDefault = true;
        emoji = "⚽";
        role = "work — Betha, code, productivity";
        workspace = "openclaw/robson";
        tts.voice = "pt-BR-AntonioNeural";
        telegram.enable = true;
      };
      jenny = {
        enable = true;
        emoji = "🎀";
        role = "personal assistant, reminders, scheduling";
        workspace = "openclaw/jenny";
        tts.voice = "en-US-JennyNeural";
        telegram.enable = true;
      };
      monster = {
        enable = true;
        emoji = "👾";
        role = "creative assistant, brainstorming, fun tasks";
        workspace = "openclaw/monster";
        tts.voice = "en-US-GuyNeural";
        telegram.enable = true;
      };
      silver = {
        enable = true;
        emoji = "🪙";
        role = "research & analysis — technical deep dives, documentation, investigation";
        workspace = "openclaw/silver";
        tts.voice = "pt-BR-FranciscaNeural";
        telegram.enable = true;
      };
    };
  };
}
