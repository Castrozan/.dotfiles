# ia-work: Automated AI work processing from Obsidian notes
# Scans vault for notes with agent-work tag and passes entire note to AI
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.services.ia-work;

  ia-work-script = pkgs.writeShellScriptBin "ia-work" (builtins.readFile ../../bin/ia-work);

  ia-work-wrapped = pkgs.writeShellScriptBin "ia-work-service" ''
    export IA_WORK_VAULT_PATH="${cfg.vaultPath}"
    export IA_WORK_TAG="${cfg.tagName}"
    export IA_WORK_HOURS="${toString cfg.hoursBack}"
    export IA_WORK_ENSURE_OBSIDIAN="${if cfg.ensureObsidian then "true" else "false"}"
    export IA_WORK_VERBOSE="${if cfg.verbose then "true" else "false"}"
    export IA_WORK_LOG_DIR="${cfg.logDir}"
    export IA_WORK_HEADLESS="${if cfg.headless then "true" else "false"}"
    export IA_WORK_TMUX_PREFIX="${cfg.tmuxPrefix}"
    exec ${ia-work-script}/bin/ia-work "$@"
  '';
in
{
  options.services.ia-work = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Enable ia-work AI instruction processor";
    };

    vaultPath = lib.mkOption {
      type = lib.types.path;
      default = "${config.home.homeDirectory}/vault";
      description = "Path to Obsidian vault";
    };

    tagName = lib.mkOption {
      type = lib.types.str;
      default = "agent-work";
      description = "Tag name to search for in notes (done tag will be {tagName}-done)";
    };

    hoursBack = lib.mkOption {
      type = lib.types.int;
      default = 24;
      description = "Look back N hours for modified notes";
    };

    ensureObsidian = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Ensure Obsidian is running before processing (for sync)";
    };

    verbose = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Enable verbose logging";
    };

    logDir = lib.mkOption {
      type = lib.types.path;
      default = "${config.home.homeDirectory}/.local/state/ia-work";
      description = "Directory for AI execution logs";
    };

    headless = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Run Claude headlessly without tmux (for systemd timer)";
    };

    tmuxPrefix = lib.mkOption {
      type = lib.types.str;
      default = "ia-work";
      description = "Prefix for tmux session names";
    };

    timer = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable ia-work systemd timer";
      };

      interval = lib.mkOption {
        type = lib.types.str;
        default = "30min";
        description = "How often to run ia-work (systemd OnUnitActiveSec format)";
      };

      persistent = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Run immediately if the last scheduled run was missed";
      };
    };
  };

  config = lib.mkIf cfg.enable {
    home.packages = [
      ia-work-wrapped
      ia-work-script
    ];

    home.activation.ia-work-log-dir = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      mkdir -p "${cfg.logDir}"
    '';

    systemd.user.services.ia-work = {
      Unit = {
        Description = "ia-work: Process AI instructions from Obsidian notes";
        After = [ "network.target" ];
      };

      Service = {
        Type = "oneshot";
        ExecStart = "${ia-work-wrapped}/bin/ia-work-service";
        Environment = [
          "HOME=${config.home.homeDirectory}"
          "PATH=${
            lib.makeBinPath [
              pkgs.coreutils
              pkgs.gnugrep
              pkgs.gnused
              pkgs.findutils
              pkgs.tmux
            ]
          }"
        ];
        SuccessExitStatus = "0 1";
      };
    };

    systemd.user.timers.ia-work = lib.mkIf cfg.timer.enable {
      Unit = {
        Description = "Timer for ia-work AI instruction processor";
      };

      Timer = {
        OnBootSec = "5min";
        OnUnitActiveSec = cfg.timer.interval;
        Persistent = cfg.timer.persistent;
        RandomizedDelaySec = "2min";
      };

      Install = {
        WantedBy = [ "timers.target" ];
      };
    };
  };
}
