{
  config,
  lib,
  pkgs,
  isNixOS,
  inputs,
  ...
}:
let
  bridgeSettings = config.clawdeDiscordVoiceBridge;
  scripts = ./scripts;
  a2aClientScripts = ../../../../agent-to-agent-communication/client/scripts;
  a2aServants = ../../../../servants;
  a2aSessionDetection = ../../../../hooks/runtime/common;
  pacePackage = inputs.herdr-pace.packages.${pkgs.stdenv.hostPlatform.system}.default;
  transcriberScripts = ../../../../../machine-configuration/media/avatar/scripts/listening;
  jessicaElevenLabsVoice = "cgSgspJ2msm6clMCkdW9";

  silverVoice = pkgs.writeShellScriptBin "silver-voice" ''
    exec ${pkgs.python312}/bin/python3 ${scripts}/silver_voice_cli.py "$@"
  '';
  discordVoice = pkgs.writeShellScriptBin "discord-voice" ''
    exec ${pkgs.python312}/bin/python3 ${scripts}/silver_voice_cli.py "$@"
  '';
in
{
  options.clawdeDiscordVoiceBridge = lib.mkOption {
    type = lib.types.nullOr (
      lib.types.submodule {
        options = {
          botTokenSecretName = lib.mkOption {
            type = lib.types.str;
            description = "Secret under ~/.secrets holding the Discord bot token.";
          };
          listenerDiscordUserId = lib.mkOption {
            type = lib.types.str;
            description = "The only Discord user whose speech the bridge hears.";
          };
          answeredGuildId = lib.mkOption {
            type = lib.types.str;
            description = "The Discord server whose voice channels the bridge joins when the listener enters one.";
          };
          conversationProfile = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Hermes profile that answers the listener's speech.";
          };
          conversationAgent = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Existing A2A peer that answers instead of a Hermes profile.";
          };
        };
      }
    );
    default = null;
    description = "Discord voice bridge carrying one listener's speech to an orchestrator and its replies back.";
  };

  config = lib.mkIf (bridgeSettings != null) {
    assertions = [
      {
        assertion =
          (bridgeSettings.conversationProfile != null) != (bridgeSettings.conversationAgent != null);
        message = "Discord voice requires exactly one conversationProfile or conversationAgent.";
      }
    ];
    home.packages = [
      silverVoice
      discordVoice
    ];

    systemd.user.services.silver-voice-bridge = lib.mkIf isNixOS {
      Unit = {
        Description = "Discord agent voice bridge";
        X-SwitchMethod = "keep-old";
      };
      Install.WantedBy = [ "default.target" ];
      Service = {
        ExecStart = "${config.hermes.unwrappedPackage.hermesVenv}/bin/python3 -m voice_bridge.bridge_daemon";
        Environment = [
          "PYTHONPATH=${scripts}:${transcriberScripts}"
          "VOICE_BRIDGE_FFMPEG=${pkgs.ffmpeg}/bin/ffmpeg"
          "VOICE_BRIDGE_OPUS_LIBRARY=${pkgs.libopus}/lib/libopus.so"
          "VOICE_BRIDGE_CONTROL_SOCKET=%t/silver-voice/control.sock"
          "VOICE_BRIDGE_LISTENER_USER_ID=${bridgeSettings.listenerDiscordUserId}"
          "VOICE_BRIDGE_ANSWERED_GUILD_ID=${bridgeSettings.answeredGuildId}"
          "VOICE_BRIDGE_TOKEN_FILE=%h/.secrets/${bridgeSettings.botTokenSecretName}"
          "VOICE_BRIDGE_CLOUD_VOICE=${jessicaElevenLabsVoice}"
        ];
        RuntimeDirectory = "silver-voice";
        RuntimeDirectoryMode = "0700";
        Restart = "on-failure";
        RestartSec = "3s";
      };
    };

    systemd.user.services.silver-voice-conductor = lib.mkIf isNixOS {
      Unit = {
        Description = "Discord agent voice call conductor";
        X-SwitchMethod = "keep-old";
        After = [ "silver-voice-bridge.service" ];
        BindsTo = [ "silver-voice-bridge.service" ];
      };
      Install.WantedBy = [ "silver-voice-bridge.service" ];
      Service = {
        ExecStart = "${pkgs.python312}/bin/python3 -m voice_bridge.call_conductor";
        Environment = [
          "PATH=/run/wrappers/bin:${config.home.profileDirectory}/bin:/run/current-system/sw/bin"
          "PYTHONPATH=${scripts}:${a2aClientScripts}:${a2aServants}:${a2aSessionDetection}:${pacePackage}/${pkgs.python312.sitePackages}"
          "VOICE_BRIDGE_CONTROL_SOCKET=%t/silver-voice/control.sock"
          "VOICE_CONDUCTOR_CONTROL_SOCKET=%t/silver-voice/conductor.sock"
          "VOICE_CONDUCTOR_HERDR_SOCKET=${config.xdg.configHome}/herdr/herdr.sock"
          "VOICE_CONDUCTOR_HERMES=${config.hermes.package}/bin/hermes"
        ]
        ++ lib.optional (
          bridgeSettings.conversationProfile != null
        ) "VOICE_CONDUCTOR_PROFILE=${bridgeSettings.conversationProfile}"
        ++ lib.optional (
          bridgeSettings.conversationAgent != null
        ) "VOICE_CONDUCTOR_AGENT=${bridgeSettings.conversationAgent}";
        WorkingDirectory = config.home.homeDirectory;
        Restart = "on-failure";
        RestartSec = "3s";
      };
    };
  };
}
