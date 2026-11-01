{
  config,
  lib,
  pkgs,
  ...
}:
let
  bridgeSettings = config.clawdeDiscordVoiceBridge;
  scripts = ./scripts;
  transcriberScripts = ../../../../../machine-configuration/media/avatar/scripts/listening;
  mediaSpeech = import ../../../../../machine-configuration/media/media-generation/speech-package.nix {
    inherit pkgs;
  };
  jessicaElevenLabsVoice = "cgSgspJ2msm6clMCkdW9";

  silverVoice = pkgs.writeShellScriptBin "silver-voice" ''
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
        };
      }
    );
    default = null;
    description = "Discord voice bridge carrying one listener's speech to an orchestrator and its replies back.";
  };

  config = lib.mkIf (bridgeSettings != null) {
    home.packages = [ silverVoice ];

    systemd.user.services.silver-voice-bridge = {
      Unit = {
        Description = "Silver Discord voice bridge";
        After = [ "avatar-transcriber.service" ];
        Requires = [ "avatar-transcriber.service" ];
      };
      Service = {
        ExecStart = "${config.hermes.unwrappedPackage.hermesVenv}/bin/python3 -m voice_bridge.bridge_daemon";
        Environment = [
          "PYTHONPATH=${scripts}:${transcriberScripts}"
          "VOICE_BRIDGE_FFMPEG=${pkgs.ffmpeg}/bin/ffmpeg"
          "VOICE_BRIDGE_OPUS_LIBRARY=${pkgs.libopus}/lib/libopus.so"
          "VOICE_BRIDGE_CONTROL_SOCKET=%t/silver-voice/control.sock"
          "VOICE_BRIDGE_LISTENER_USER_ID=${bridgeSettings.listenerDiscordUserId}"
          "VOICE_BRIDGE_TOKEN_FILE=%h/.secrets/${bridgeSettings.botTokenSecretName}"
          "VOICE_BRIDGE_MEDIA_SPEECH=${mediaSpeech}/bin/media-speech"
          "VOICE_BRIDGE_CLOUD_VOICE=${jessicaElevenLabsVoice}"
        ];
        RuntimeDirectory = "silver-voice";
        RuntimeDirectoryMode = "0700";
        Restart = "on-failure";
        RestartSec = "3s";
      };
    };
  };
}
