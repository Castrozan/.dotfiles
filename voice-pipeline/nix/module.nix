{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.voice-pipeline;
  openclaw = config.openclaw;

  agentVoicesJson = builtins.toJSON (lib.mapAttrs (_name: agentCfg: agentCfg.openaiVoice) cfg.agents);

  wakeWordsJson = builtins.toJSON cfg.wakeWords;

  environmentFile = pkgs.writeText "voice-pipeline-env" ''
    VOICE_PIPELINE_GATEWAY_URL=http://localhost:${toString openclaw.gatewayPort}
    VOICE_PIPELINE_GATEWAY_TOKEN_FILE=/run/agenix/openclaw-gateway-token
    VOICE_PIPELINE_DEFAULT_AGENT=${cfg.defaultAgent}
    VOICE_PIPELINE_DEEPGRAM_API_KEY_FILE=/run/agenix/deepgram-api-key
    VOICE_PIPELINE_OPENAI_API_KEY_FILE=/run/agenix/openai-api-key
    VOICE_PIPELINE_TTS_VOICE=${cfg.ttsVoice}
    VOICE_PIPELINE_WAKE_WORDS=${wakeWordsJson}
    VOICE_PIPELINE_CONVERSATION_WINDOW_SECONDS=${toString cfg.conversationWindowSeconds}
    VOICE_PIPELINE_MAX_HISTORY_TURNS=${toString cfg.maxHistoryTurns}
    VOICE_PIPELINE_CAPTURE_DEVICE=${cfg.captureDevice}
    VOICE_PIPELINE_BARGE_IN_ENABLED=${if cfg.bargeInEnabled then "true" else "false"}
    VOICE_PIPELINE_STT_ENGINE=${cfg.sttEngine}
    VOICE_PIPELINE_AGENT_VOICES=${agentVoicesJson}
    VOICE_PIPELINE_MODEL=${cfg.model}
  '';
in
{
  options.services.voice-pipeline = {
    enable = lib.mkEnableOption "Voice Pipeline real-time conversational AI";

    defaultAgent = lib.mkOption {
      type = lib.types.str;
      default = "jarvis";
    };

    wakeWords = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ "jarvis" ];
    };

    ttsVoice = lib.mkOption {
      type = lib.types.str;
      default = "onyx";
    };

    model = lib.mkOption {
      type = lib.types.str;
      default = "anthropic/claude-sonnet-4-5";
    };

    sttEngine = lib.mkOption {
      type = lib.types.enum [
        "deepgram"
        "openai-whisper"
      ];
      default = "deepgram";
    };

    captureDevice = lib.mkOption {
      type = lib.types.str;
      default = "echo-cancel-source";
    };

    conversationWindowSeconds = lib.mkOption {
      type = lib.types.float;
      default = 15.0;
    };

    maxHistoryTurns = lib.mkOption {
      type = lib.types.int;
      default = 20;
    };

    bargeInEnabled = lib.mkOption {
      type = lib.types.bool;
      default = true;
    };

    agents = lib.mkOption {
      type = lib.types.attrsOf (
        lib.types.submodule {
          options.openaiVoice = lib.mkOption {
            type = lib.types.str;
            default = "onyx";
          };
        }
      );
      default = { };
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.user.services.voice-pipeline = {
      Unit = {
        Description = "Voice Pipeline - Real-time conversational AI";
        After = [ "pipewire.service" ];
      };
      Service = {
        Type = "simple";
        EnvironmentFile = toString environmentFile;
        ExecStart = "${pkgs.lib.getExe (
          pkgs.writeShellScriptBin "voice-pipeline-start" ''
            exec voice-pipeline
          ''
        )}";
        Restart = "on-failure";
        RestartSec = 5;
      };
      Install.WantedBy = [ ];
    };
  };
}
