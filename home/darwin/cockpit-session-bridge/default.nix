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

  maintainPersistentSessionScript = ../../../nixos/modules/cockpit-session-bridge/scripts/maintain_persistent_session.sh;
  cockpitSessionBridgePackage = ../../../nixos/modules/cockpit-session-bridge/scripts/cockpit_session_bridge;

  tmuxTemporaryDirectory = "/tmp";

  keepaliveExecutableSearchPath = "${pkgs.tmux}/bin:${pkgs.coreutils}/bin:/usr/bin:/bin";

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

    persistentSession = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = cockpitSessionBridgeConfig.enable;
        description = "Keep an always-on tmux session running opencode so the cockpit Internal terminal attaches to one shared live TUI instead of spawning a throwaway shell per connection.";
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
        description = "Shell command tmux runs as the persistent session's only window; a login non-interactive bash inherits the owner's PATH so opencode resolves, and exec replaces the shell so the window dies with opencode and the keepalive restarts it.";
      };
    };
  };

  config = lib.mkIf cockpitSessionBridgeConfig.enable {
    launchd.agents.jarvis-session-tmux = lib.mkIf persistentSessionConfig.enable {
      enable = true;
      config = {
        Label = "com.dotfiles.jarvis-session-tmux";
        ProgramArguments = [
          "${pkgs.bashInteractive}/bin/bash"
          "${maintainPersistentSessionScript}"
          persistentSessionConfig.socketName
          persistentSessionConfig.sessionName
          "${persistentSessionTmuxConfiguration}"
        ];
        EnvironmentVariables = {
          PATH = keepaliveExecutableSearchPath;
          TMUX_TMPDIR = tmuxTemporaryDirectory;
          JARVIS_PERSISTENT_SESSION_COMMAND = persistentSessionConfig.command;
        };
        KeepAlive = true;
        RunAtLoad = true;
        StandardOutPath = "/tmp/jarvis-session-tmux.log";
        StandardErrorPath = "/tmp/jarvis-session-tmux.log";
      };
    };

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
