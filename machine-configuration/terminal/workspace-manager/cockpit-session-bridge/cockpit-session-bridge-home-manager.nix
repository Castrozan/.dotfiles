{
  config,
  lib,
  pkgs,
  inputs,
  ...
}:
let
  cockpitSessionBridgeConfig = config.custom.cockpitSessionBridge;

  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
  herdrClientPackage =
    (import ../herdr/herdr-client-package.nix {
      inherit pkgs herdrPackage;
    }).package;

  pythonWithWebsockets = pkgs.python3.withPackages (pythonPackages: [ pythonPackages.websockets ]);

  cockpitSessionBridgePackage = ./scripts/cockpit_session_bridge;

  tmuxTemporaryDirectory = "/tmp";

in
{
  options.custom.cockpitSessionBridge = {
    enable = lib.mkEnableOption "the owner-only cockpit bridge for terminal sessions and machine inventory";

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
      description = "Argument vector launched inside a pseudoterminal for an owner connection without a selected terminal.";
    };

    allowedRequestOrigin = lib.mkOption {
      type = lib.types.str;
      default = "https://lucaszanoni.com";
      description = "Exact browser Origin the bridge accepts; an empty string disables the check and is intended for local testing only.";
    };

    tmuxEnumerationSocket = lib.mkOption {
      type = lib.types.str;
      default = "cockpit";
      description = "tmux socket name the lifecycle list-sessions enumeration reads; an empty string targets the owner's default interactive socket so the workspace can see his real claude sessions.";
    };

    tmuxMutationSocket = lib.mkOption {
      type = lib.types.str;
      default = "cockpit";
      description = "tmux socket name every destructive lifecycle mutation is confined to; kept on the sandbox cockpit socket so the website can never kill the owner's real sessions even when enumeration reads his default socket.";
    };

    tmuxRemoteSshHost = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "When non-empty, the SSH destination (user@host) the bridge runs every enumeration and attach tmux command through, so a bridge on one host can list and drive another host's real sessions over SSH without exposing that host's loopback bridge to the network; empty keeps all tmux commands local. Destructive mutations always stay on the local sandbox mutation socket and are never forwarded, so the remote host's real sessions can be read and attached but never killed.";
    };

    herdrSessionName = lib.mkOption {
      type = lib.types.str;
      default = "default";
      description = "herdr session the lifecycle enumeration and attach target when herdr is the live multiplexer; herdr hosts the whole fleet on one shared server session, so this is the session every cockpit workspace lives under.";
    };

  };

  config = lib.mkIf cockpitSessionBridgeConfig.enable {
    launchd.agents.cockpit-session-bridge = {
      enable = true;
      config = {
        Label = "com.dotfiles.cockpit-session-bridge";
        ProgramArguments = [
          "${pythonWithWebsockets}/bin/python"
          "${cockpitSessionBridgePackage}"
        ];
        EnvironmentVariables = {
          COCKPIT_SESSION_BRIDGE_LISTEN_ADDRESS = cockpitSessionBridgeConfig.listenAddress;
          COCKPIT_SESSION_BRIDGE_LISTEN_PORT = toString cockpitSessionBridgeConfig.listenPort;
          COCKPIT_SESSION_BRIDGE_COMMAND_JSON = builtins.toJSON cockpitSessionBridgeConfig.sessionCommand;
          COCKPIT_SESSION_BRIDGE_ALLOWED_ORIGIN = cockpitSessionBridgeConfig.allowedRequestOrigin;
          COCKPIT_SESSION_BRIDGE_TMUX_PATH = "${pkgs.tmux}/bin/tmux";
          COCKPIT_SESSION_BRIDGE_TMUX_ENUMERATION_SOCKET = cockpitSessionBridgeConfig.tmuxEnumerationSocket;
          COCKPIT_SESSION_BRIDGE_TMUX_MUTATION_SOCKET = cockpitSessionBridgeConfig.tmuxMutationSocket;
          COCKPIT_SESSION_BRIDGE_TMUX_REMOTE_SSH_HOST = cockpitSessionBridgeConfig.tmuxRemoteSshHost;
          COCKPIT_SESSION_BRIDGE_HERDR_PATH = "${herdrClientPackage}/bin/herdr";
          COCKPIT_SESSION_BRIDGE_HERDR_SESSION = cockpitSessionBridgeConfig.herdrSessionName;
          TMUX_TMPDIR = tmuxTemporaryDirectory;
        };
        KeepAlive = true;
        RunAtLoad = true;
        StandardOutPath = "/tmp/cockpit-session-bridge.log";
        StandardErrorPath = "/tmp/cockpit-session-bridge.log";
      };
    };
  };
}
