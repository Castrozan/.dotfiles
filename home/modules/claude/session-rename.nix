# claude-session-rename: Automated session naming for Claude Code
# Uses Claude CLI to generate short descriptive names for sessions
{ config, lib, pkgs, ... }:

let
  cfg = config.services.claude-session-rename;

  session-rename-script = pkgs.writeShellScriptBin "claude-session-rename"
    (builtins.readFile ../../../bin/claude-session-rename);

  session-rename-wrapped = pkgs.writeShellScriptBin "claude-session-rename-service" ''
    export CLAUDE_SESSION_RENAME_MAX_LENGTH="${toString cfg.maxLength}"
    export CLAUDE_SESSION_RENAME_MIN_LENGTH="${toString cfg.minLength}"
    export CLAUDE_SESSION_RENAME_VERBOSE="${if cfg.verbose then "true" else "false"}"
    export CLAUDE_SESSION_RENAME_DRY_RUN="false"
    export PATH="${lib.makeBinPath [ pkgs.coreutils pkgs.gnugrep pkgs.gnused pkgs.jq pkgs.claude-code ]}:$PATH"
    exec ${session-rename-script}/bin/claude-session-rename "$@"
  '';
in
{
  options.services.claude-session-rename = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Enable automatic Claude Code session renaming";
    };

    maxLength = lib.mkOption {
      type = lib.types.int;
      default = 50;
      description = "Maximum length for generated session names";
    };

    minLength = lib.mkOption {
      type = lib.types.int;
      default = 60;
      description = "Minimum firstPrompt length to trigger renaming (shorter prompts are kept as-is)";
    };

    verbose = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Enable verbose logging";
    };

    timer = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable systemd timer for automatic renaming";
      };

      interval = lib.mkOption {
        type = lib.types.str;
        default = "1min";
        description = "How often to run session rename (systemd OnUnitActiveSec format)";
      };

      persistent = lib.mkOption {
        type = lib.types.bool;
        default = false;
        description = "Run immediately if the last scheduled run was missed";
      };
    };
  };

  config = lib.mkIf cfg.enable {
    home.packages = [ session-rename-wrapped session-rename-script ];

    systemd.user.services.claude-session-rename = {
      Unit = {
        Description = "Claude Code session auto-renamer";
      };

      Service = {
        Type = "oneshot";
        ExecStart = "${session-rename-wrapped}/bin/claude-session-rename-service";
        Environment = [
          "HOME=${config.home.homeDirectory}"
        ];
        # Allow failures (e.g., network issues, Claude CLI not responding)
        SuccessExitStatus = "0 1";
      };
    };

    systemd.user.timers.claude-session-rename = lib.mkIf cfg.timer.enable {
      Unit = {
        Description = "Timer for Claude Code session renamer";
      };

      Timer = {
        OnBootSec = "2min";
        OnUnitActiveSec = cfg.timer.interval;
        Persistent = cfg.timer.persistent;
      };

      Install = {
        WantedBy = [ "timers.target" ];
      };
    };
  };
}
