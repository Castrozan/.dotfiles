{
  config,
  lib,
  pkgs,
  isNixOS,
  hostname,
  ...
}:
let
  bridgeSettings = config.clawdeDiscordVoiceBridge;
  scripts = ./scripts;

  identitySpecifications = pkgs.writeText "discord-voice-identities.json" (
    builtins.toJSON (
      [
        {
          name = "primary";
          tokenFile = "${config.home.homeDirectory}/.secrets/${bridgeSettings.botTokenSecretName}";
          ownerHost = hostname;
          listenerUserId = bridgeSettings.listenerDiscordUserId;
          guildId = bridgeSettings.answeredGuildId;
          preferredAgent = bridgeSettings.conversationProfile;
        }
      ]
      ++ lib.mapAttrsToList (name: identity: {
        inherit name;
        tokenFile = "${config.home.homeDirectory}/.secrets/${identity.botTokenSecretName}";
        inherit (identity)
          ownerHost
          listenerUserId
          guildId
          preferredAgent
          ;
      }) config.clawdeDiscordVoiceIdentities
    )
  );

  silverVoice = pkgs.writeShellScriptBin "silver-voice" ''
    exec ${pkgs.python312}/bin/python3 ${scripts}/silver_voice_cli.py "$@"
  '';
  discordVoice = pkgs.writeShellScriptBin "discord-voice" ''
    exec ${pkgs.python312}/bin/python3 ${scripts}/silver_voice_cli.py "$@"
  '';
in
{
  imports = [ ./silver-voice-holder.nix ];

  options.clawdeDiscordVoiceIdentities = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options = {
          botTokenSecretName = lib.mkOption { type = lib.types.str; };
          ownerHost = lib.mkOption { type = lib.types.str; };
          listenerUserId = lib.mkOption { type = lib.types.str; };
          guildId = lib.mkOption { type = lib.types.str; };
          preferredAgent = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
          };
        };
      }
    );
    default = { };
    description = "Explicit bot voice grants, fenced to one owning host, listener and guild.";
  };
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
          silverChannelName = lib.mkOption {
            type = lib.types.str;
            default = "silver";
            description = "Voice channel of the answered server where the listener asks for Silver by name; the bridge starts the avatar voice holder only when the listener enters it.";
          };
          conversationProfile = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Hermes profile whose Silver holds the avatar floor in the silver voice channel.";
          };
        };
      }
    );
    default = null;
    description = "Discord transport for the avatar: bot identities, joining the listener's channel, capture and playback of call audio. Conversations run through the avatar.";
  };

  config = lib.mkIf (bridgeSettings != null) {
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
          "PYTHONPATH=${scripts}"
          "VOICE_BRIDGE_FFMPEG=${pkgs.ffmpeg}/bin/ffmpeg"
          "VOICE_BRIDGE_OPUS_LIBRARY=${pkgs.libopus}/lib/libopus.so"
          "PATH=${config.home.profileDirectory}/bin:/run/current-system/sw/bin"
          "VOICE_BRIDGE_CONTROL_SOCKET=%t/silver-voice/control.sock"
          "VOICE_BRIDGE_SILVER_CHANNEL_NAME=${bridgeSettings.silverChannelName}"
          "VOICE_BRIDGE_LISTENER_USER_ID=${bridgeSettings.listenerDiscordUserId}"
          "VOICE_BRIDGE_ANSWERED_GUILD_ID=${bridgeSettings.answeredGuildId}"
          "VOICE_BRIDGE_IDENTITIES=${identitySpecifications}"
          "VOICE_BRIDGE_HOST=${hostname}"
        ];
        RuntimeDirectory = "silver-voice";
        RuntimeDirectoryMode = "0700";
        TimeoutStopSec = "30s";
        Restart = "on-failure";
        RestartSec = "3s";
      };
    };
  };
}
