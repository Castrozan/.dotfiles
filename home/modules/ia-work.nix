# ia-work: Automated AI work processing from Obsidian notes
# Periodically scans vault for notes with ia-work tag and executes AI instructions
{ config, lib, pkgs, ... }:

let
  cfg = config.services.ia-work;

  # Create the script with all dependencies available
  ia-work-script = pkgs.writeShellScriptBin "ia-work" (builtins.readFile ../../bin/ia-work);

  # Script with wrapped environment
  ia-work-wrapped = pkgs.writeShellScriptBin "ia-work-service" ''
    export IA_WORK_VAULT_PATH="${cfg.vaultPath}"
    export IA_WORK_AI_CLI="${cfg.aiCli}"
    export IA_WORK_TAG="${cfg.tagName}"
    export IA_WORK_HOURS="${toString cfg.hoursBack}"
    export IA_WORK_ENSURE_OBSIDIAN="${if cfg.ensureObsidian then "true" else "false"}"
    export IA_WORK_VERBOSE="${if cfg.verbose then "true" else "false"}"
    export IA_WORK_LOG_DIR="${cfg.logDir}"
    export PATH="${lib.makeBinPath cfg.extraPackages}:$PATH"
    exec ${ia-work-script}/bin/ia-work "$@"
  '';
in
{
  options.services.ia-work = {
    enable = lib.mkEnableOption "ia-work AI instruction processor";

    vaultPath = lib.mkOption {
      type = lib.types.path;
      default = "${config.home.homeDirectory}/vault";
      description = "Path to Obsidian vault";
    };

    aiCli = lib.mkOption {
      type = lib.types.str;
      default = "claude -p";
      description = "AI CLI command to execute instructions (e.g., 'claude -p', 'opencode -p')";
    };

    tagName = lib.mkOption {
      type = lib.types.str;
      default = "ia-work";
      description = "Tag name to search for in notes";
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

    timer = {
      enable = lib.mkEnableOption "ia-work systemd timer";

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

    extraPackages = lib.mkOption {
      type = lib.types.listOf lib.types.package;
      default = [ ];
      description = "Additional packages to include in PATH for AI CLI";
    };
  };

  config = lib.mkIf cfg.enable {
    # Install the script
    home.packages = [ ia-work-wrapped ia-work-script ];

    # Create log directory
    home.activation.ia-work-log-dir = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      mkdir -p "${cfg.logDir}"
    '';

    # Systemd user service
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
          "PATH=${lib.makeBinPath (cfg.extraPackages ++ [ pkgs.coreutils pkgs.gnugrep pkgs.gnused pkgs.perl pkgs.findutils ])}"
        ];
        # Don't fail if no work to do
        SuccessExitStatus = "0 1";
      };
    };

    # Systemd timer (optional)
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
