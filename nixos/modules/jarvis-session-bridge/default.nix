{
  config,
  lib,
  pkgs,
  ...
}:
let
  jarvisSessionBridgeConfig = config.custom.jarvisSessionBridge;
  pythonWithWebsockets = pkgs.python3.withPackages (pythonPackages: [ pythonPackages.websockets ]);
in
{
  options.custom.jarvisSessionBridge = {
    enable = lib.mkEnableOption "the Jarvis cockpit session bridge that streams a local login shell over a loopback websocket for the owner-only cockpit Internal terminal";

    listenAddress = lib.mkOption {
      type = lib.types.str;
      default = "127.0.0.1";
      description = "Loopback address the bridge binds, so only a co-located Cloudflare Tunnel connector reaches it and no other host on the network can.";
    };

    listenPort = lib.mkOption {
      type = lib.types.port;
      default = 8787;
      description = "Loopback port the bridge listens on for the co-located Cloudflare Tunnel connector.";
    };

    sessionCommand = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [
        "${pkgs.bashInteractive}/bin/bash"
        "-il"
      ];
      description = "Argument vector launched inside a pseudoterminal for each accepted owner session.";
    };

    allowedRequestOrigin = lib.mkOption {
      type = lib.types.str;
      default = "https://lucaszanoni.com";
      description = "Exact browser Origin the bridge accepts; an empty string disables the check and is intended for local testing only.";
    };

    serviceUser = lib.mkOption {
      type = lib.types.str;
      default = "zanoni";
      description = "Unprivileged user the session shell runs as.";
    };
  };

  config = lib.mkIf jarvisSessionBridgeConfig.enable {
    systemd.services.jarvis-session-bridge = {
      description = "Jarvis cockpit session bridge";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];
      environment = {
        JARVIS_SESSION_BRIDGE_LISTEN_ADDRESS = jarvisSessionBridgeConfig.listenAddress;
        JARVIS_SESSION_BRIDGE_LISTEN_PORT = toString jarvisSessionBridgeConfig.listenPort;
        JARVIS_SESSION_BRIDGE_COMMAND_JSON = builtins.toJSON jarvisSessionBridgeConfig.sessionCommand;
        JARVIS_SESSION_BRIDGE_ALLOWED_ORIGIN = jarvisSessionBridgeConfig.allowedRequestOrigin;
      };
      serviceConfig = {
        ExecStart = "${pythonWithWebsockets}/bin/python ${./scripts/jarvis_session_bridge}";
        Restart = "on-failure";
        RestartSec = 2;
        User = jarvisSessionBridgeConfig.serviceUser;
      };
    };
  };
}
