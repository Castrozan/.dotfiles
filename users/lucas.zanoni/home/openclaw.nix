{ config, ... }:
{
  openclaw = {
    configPatches = {
      ".channels.discord.accounts.robson.allowFrom" = [ "284143065877184512" ];
      ".channels.discord.accounts.robson.guilds.998625197802410094.users" = [ "284143065877184512" ];
    };

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
          model = "opus-4.6";
        }
      ];
    };

    userName = "Lucas";
    gatewayPort = 18790;
    gatewayService.enable = true;
    coreRulesContent = builtins.readFile ../../../agents/core.md;
    defaults.model = {
      primary = "anthropic/claude-opus-4-6";
      heartbeat = "openai-codex/gpt-5.3-codex";
      subagents = "openai-codex/gpt-5.3-codex";
    };
    agents = {
      robson = {
        enable = true;
        isDefault = true;
        emoji = "⚽";
        role = "work — Betha, code, productivity";
        workspace = "openclaw/robson";
        tts.voice = "pt-BR-AntonioNeural";
        telegram.enable = true;
        discord = {
          enable = true;
          voice.enable = true;
          guilds."998625197802410094" = {
            slug = "anotacao";
            requireMention = true;
          };
        };
      };
      jenny = {
        enable = true;
        emoji = "🎀";
        role = "personal assistant, reminders, scheduling";
        model.primary = "anthropic/claude-sonnet-4-6";
        workspace = "openclaw/jenny";
        tts.voice = "en-US-JennyNeural";
        telegram.enable = true;
        discord = {
          enable = true;
          voice.enable = true;
        };
      };
      monster = {
        enable = true;
        emoji = "👾";
        role = "creative assistant, brainstorming, fun tasks";
        model.primary = "anthropic/claude-sonnet-4-6";
        workspace = "openclaw/monster";
        tts.voice = "en-US-GuyNeural";
        telegram.enable = true;
        discord = {
          enable = true;
          voice.enable = true;
        };
      };
      silver = {
        enable = true;
        emoji = "🪙";
        role = "research & analysis — technical deep dives, documentation, investigation";
        model.primary = "anthropic/claude-sonnet-4-6";
        workspace = "openclaw/silver";
        tts.voice = "pt-BR-FranciscaNeural";
        telegram.enable = true;
        discord = {
          enable = true;
          voice.enable = true;
        };
      };
    };
  };

  systemd.user.services.discord-vc-tts-bridge = {
    Unit = {
      Description = "Discord VC TTS bridge for robson";
      After = [
        "openclaw-gateway.service"
        "network-online.target"
      ];
      Wants = [
        "openclaw-gateway.service"
        "network-online.target"
      ];
    };
    Service = {
      ExecStart = "${config.home.homeDirectory}/.dotfiles/scripts/discord-vc-tts-bridge.cjs";
      Restart = "always";
      RestartSec = 3;
      Environment = [
        "NODE_PATH=/home/lucas.zanoni/.local/share/openclaw-npm/lib/node_modules"
        "DISCORD_VC_GUILD_ID=998625197802410094"
        "DISCORD_VC_TEXT_CHANNEL_ID=998625197802410097"
        "DISCORD_VC_CHANNEL_ID=998625197802410098"
        "DISCORD_VC_TTS_VOICE=pt-BR-AntonioNeural"
      ];
    };
    Install.WantedBy = [ "default.target" ];
  };
}
