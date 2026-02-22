{ config, ... }:
let
  opusModel = "anthropic/claude-opus-4-6";
  sonnetModel = "anthropic/claude-sonnet-4-6";
  codexModel = "openai-codex/gpt-5.3-codex";

  robsonModelPrimary = opusModel;
  jennyModelPrimary = sonnetModel;
  monsterModelPrimary = sonnetModel;
  silverModelPrimary = sonnetModel;

  lucasDiscordUserId = "284143065877184512";
  robsonDiscordGuildId = "998625197802410094";
  robsonDiscordTextChannelId = "998625197802410097";
  robsonDiscordVoiceChannelId = "998625197802410098";
  robsonTtsVoice = "pt-BR-AntonioNeural";
in
{
  openclaw = {
    configPatches = {
      ".channels.discord.accounts.robson.allowFrom" = [ lucasDiscordUserId ];
      ".channels.discord.accounts.robson.guilds.${robsonDiscordGuildId}.users" = [ lucasDiscordUserId ];
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
          model = robsonModelPrimary;
        }
        {
          id = "jenny";
          emoji = "🎀";
          model = jennyModelPrimary;
        }
        {
          id = "monster";
          emoji = "👾";
          model = monsterModelPrimary;
        }
        {
          id = "silver";
          emoji = "🪙";
          model = silverModelPrimary;
        }
      ];
    };

    userName = "Lucas";
    gatewayPort = 18790;
    gatewayService.enable = true;
    coreRulesContent = builtins.readFile ../../../agents/core.md;
    defaults.model = {
      primary = opusModel;
      heartbeat = codexModel;
      subagents = codexModel;
    };
    agents = {
      robson = {
        enable = true;
        isDefault = true;
        emoji = "⚽";
        role = "work — Betha, code, productivity";
        model.primary = robsonModelPrimary;
        workspace = "openclaw/robson";
        tts.voice = robsonTtsVoice;
        telegram.enable = true;
        discord = {
          enable = true;
          voice.enable = true;
          guilds."${robsonDiscordGuildId}" = {
            slug = "anotacao";
            requireMention = true;
          };
        };
      };
      jenny = {
        enable = true;
        emoji = "🎀";
        role = "full-stack personal agent — coding, monitoring, automation, scheduling";
        model.primary = jennyModelPrimary;
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
        model.primary = monsterModelPrimary;
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
        model.primary = silverModelPrimary;
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
        "NODE_PATH=${config.home.homeDirectory}/.local/share/openclaw-npm/lib/node_modules"
        "DISCORD_VC_GUILD_ID=${robsonDiscordGuildId}"
        "DISCORD_VC_TEXT_CHANNEL_ID=${robsonDiscordTextChannelId}"
        "DISCORD_VC_CHANNEL_ID=${robsonDiscordVoiceChannelId}"
        "DISCORD_VC_TTS_VOICE=${robsonTtsVoice}"
      ];
    };
    Install.WantedBy = [ "default.target" ];
  };
}
