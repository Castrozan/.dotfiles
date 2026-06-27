{
  config,
  lib,
  pkgs,
  ...
}:
let
  cockpitSessionBridgeConfig = config.custom.cockpitSessionBridge;
  persistentSessionConfig = cockpitSessionBridgeConfig.persistentSession;
  pythonWithWebsockets = pkgs.python3.withPackages (pythonPackages: [ pythonPackages.websockets ]);

  tmuxTemporaryDirectory = "/tmp";

  persistentSessionTmuxConfiguration = pkgs.writeText "jarvis-persistent-session.tmux.conf" ''
    set -g window-size smallest
    set -g status off
    set -g mouse on
    set -g escape-time 0
    set -g default-terminal "tmux-256color"
    set -g history-limit 50000
    set -g destroy-unattached off
  '';
in
{
  options.custom.cockpitSessionBridge = {
    enable = lib.mkEnableOption "the cockpit session bridge that streams the persistent opencode terminal over a loopback websocket for the owner-only cockpit Internal terminal";

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
        "${pkgs.tmux}/bin/tmux"
        "-L"
        persistentSessionConfig.socketName
        "attach-session"
        "-t"
        persistentSessionConfig.sessionName
      ];
      description = "Argument vector launched inside a pseudoterminal for each accepted owner session; by default it attaches a client to the always-on opencode tmux session so every owner connection shares the same live terminal.";
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

    persistentSession = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = cockpitSessionBridgeConfig.enable;
        description = "Keep an always-on tmux session running opencode so the cockpit Internal terminal attaches to one shared live TUI, the way the clawde agents stay resident, instead of spawning a throwaway shell per connection.";
      };

      socketName = lib.mkOption {
        type = lib.types.str;
        default = "jarvis";
        description = "tmux socket name the persistent session lives on and the bridge attaches to, kept distinct from the owner's interactive default socket.";
      };

      sessionName = lib.mkOption {
        type = lib.types.str;
        default = "jarvis";
        description = "tmux session name holding the always-on opencode TUI.";
      };

      command = lib.mkOption {
        type = lib.types.str;
        default = "${pkgs.bashInteractive}/bin/bash -lc 'exec opencode'";
        description = "Shell command tmux runs as the persistent session's only window; a login non-interactive bash inherits the owner's PATH so opencode resolves, while staying non-interactive to skip the login screensaver, and exec replaces the shell so the window dies with opencode and the keepalive restarts it.";
      };
    };
  };

  config = lib.mkIf cockpitSessionBridgeConfig.enable {
    systemd.services.jarvis-session-tmux = lib.mkIf persistentSessionConfig.enable {
      description = "Jarvis always-on opencode tmux session";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];
      path = [
        pkgs.tmux
        pkgs.bashInteractive
        pkgs.coreutils
      ];
      environment = {
        TMUX_TMPDIR = tmuxTemporaryDirectory;
        JARVIS_PERSISTENT_SESSION_COMMAND = persistentSessionConfig.command;
      };
      serviceConfig = {
        ExecStart = "${pkgs.bashInteractive}/bin/bash ${./scripts/maintain_persistent_session.sh} ${persistentSessionConfig.socketName} ${persistentSessionConfig.sessionName} ${persistentSessionTmuxConfiguration}";
        Restart = "always";
        RestartSec = 5;
        User = cockpitSessionBridgeConfig.serviceUser;
      };
    };

    systemd.services.cockpit-session-bridge = {
      description = "cockpit session bridge";
      wantedBy = [ "multi-user.target" ];
      after = [
        "network.target"
        "jarvis-session-tmux.service"
      ];
      wants = lib.optional persistentSessionConfig.enable "jarvis-session-tmux.service";
      environment = {
        COCKPIT_SESSION_BRIDGE_LISTEN_ADDRESS = cockpitSessionBridgeConfig.listenAddress;
        COCKPIT_SESSION_BRIDGE_LISTEN_PORT = toString cockpitSessionBridgeConfig.listenPort;
        COCKPIT_SESSION_BRIDGE_COMMAND_JSON = builtins.toJSON cockpitSessionBridgeConfig.sessionCommand;
        COCKPIT_SESSION_BRIDGE_ALLOWED_ORIGIN = cockpitSessionBridgeConfig.allowedRequestOrigin;
        COCKPIT_SESSION_BRIDGE_TMUX_PATH = "${pkgs.tmux}/bin/tmux";
        TMUX_TMPDIR = tmuxTemporaryDirectory;
      };
      serviceConfig = {
        ExecStart = "${pythonWithWebsockets}/bin/python ${./scripts/cockpit_session_bridge}";
        Restart = "on-failure";
        RestartSec = 2;
        User = cockpitSessionBridgeConfig.serviceUser;
      };
    };
  };
}
