{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.hey-bot;

  keywordsPattern = builtins.concatStringsSep "|" cfg.keywords;

  heyBotDaemon = pkgs.writeShellApplication {
    name = "hey-bot";
    runtimeInputs = with pkgs; [
      sox
      whisper-cpp
      python3Packages.edge-tts
      mpv
      curl
      jq
      libnotify
      wireplumber
      perl
    ];
    runtimeEnv = {
      HEY_BOT_WHISPER_MODEL = cfg.whisperModel;
      HEY_BOT_KEYWORDS_PATTERN = keywordsPattern;
      HEY_BOT_GATEWAY_URL = cfg.gatewayUrl;
      HEY_BOT_GATEWAY_TOKEN_FILE = cfg.gatewayTokenFile;
      HEY_BOT_AGENT_ID = cfg.agentId;
      HEY_BOT_TTS_VOICE = cfg.ttsVoice;
      HEY_BOT_MODEL = cfg.model;
      HEY_BOT_TRANSCRIPTION_DIR = cfg.transcriptionDir;
      HEY_BOT_MAX_LOG_SIZE = toString cfg.maxLogFileSize;
    };
    text = builtins.readFile ./scripts/hey-bot;
  };

  heyBotLog = pkgs.writeShellApplication {
    name = "hey-bot-log";
    runtimeEnv = {
      HEY_BOT_TRANSCRIPTION_DIR = cfg.transcriptionDir;
    };
    text = builtins.readFile ./scripts/hey-bot-log;
  };

  heyBotToggle = pkgs.writeShellApplication {
    name = "hey-bot-toggle";
    runtimeInputs = with pkgs; [
      systemd
      libnotify
    ];
    text = ''
      readonly SERVICE_NAME="hey-bot.service"

      if systemctl --user is-active --quiet "$SERVICE_NAME"; then
        systemctl --user stop "$SERVICE_NAME"
        notify-send "Hey Bot" "Disabled" 2>/dev/null || true
        echo "hey-bot: disabled"
      else
        systemctl --user start "$SERVICE_NAME"
        notify-send "Hey Bot" "Enabled" 2>/dev/null || true
        echo "hey-bot: enabled"
      fi
    '';
  };

  heyBotPushToTalk = pkgs.writeShellApplication {
    name = "hey-bot-ptt";
    runtimeInputs = with pkgs; [
      python3Packages.edge-tts
      mpv
      curl
      jq
      libnotify
      wireplumber
      wl-clipboard
    ];
    runtimeEnv = {
      HEY_BOT_GATEWAY_URL = cfg.gatewayUrl;
      HEY_BOT_GATEWAY_TOKEN_FILE = cfg.gatewayTokenFile;
      HEY_BOT_AGENT_ID = cfg.agentId;
      HEY_BOT_TTS_VOICE = cfg.ttsVoice;
      HEY_BOT_MODEL = cfg.model;
    };
    text = builtins.readFile ./scripts/hey-bot-ptt;
  };
in
{
  options.services.hey-bot = {
    enable = lib.mkEnableOption "Hey Bot always-on voice assistant";

    keywords = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      description = "Keywords to listen for (case-insensitive, used as grep -E alternation)";
    };

    gatewayUrl = lib.mkOption {
      type = lib.types.str;
      default = "http://localhost:18789";
    };

    gatewayTokenFile = lib.mkOption {
      type = lib.types.str;
      default = "${config.home.homeDirectory}/.secrets/voice-gateway-token";
    };

    agentId = lib.mkOption {
      type = lib.types.str;
      default = "main";
    };

    ttsVoice = lib.mkOption {
      type = lib.types.str;
      default = "en-US-JennyNeural";
    };

    model = lib.mkOption {
      type = lib.types.str;
      default = "openai-codex/gpt-5.3-codex";
    };

    whisperModel = lib.mkOption {
      type = lib.types.str;
      default = "${config.home.homeDirectory}/.cache/whisper-cpp/models/ggml-base.bin";
    };

    transcriptionDir = lib.mkOption {
      type = lib.types.str;
      default = "${config.home.homeDirectory}/.local/share/hey-bot/transcriptions";
    };

    maxLogFileSize = lib.mkOption {
      type = lib.types.int;
      default = 1048576;
    };
  };

  config = lib.mkIf cfg.enable {
    home.packages = [
      heyBotDaemon
      heyBotPushToTalk
      heyBotLog
      heyBotToggle
    ];

    systemd.user.services.hey-bot = {
      Unit = {
        Description = "Hey Bot - Always-on voice assistant";
        After = [ "pipewire.service" ];
      };
      Service = {
        Type = "simple";
        ExecStart = "${heyBotDaemon}/bin/hey-bot";
        Restart = "on-failure";
        RestartSec = 5;
      };
      Install.WantedBy = [ ];
    };
  };
}
