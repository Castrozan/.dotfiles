{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  cfg = openclaw.scheduledBackup;

  nodejs = pkgs.nodejs_22;
  npmPrefix = "$HOME/.local/share/openclaw-npm";
  backupDirectory = "$HOME/.local/share/openclaw-backups";
  maximumBackupsToKeep = 7;

  scheduledBackupScript = pkgs.writeShellScript "openclaw-scheduled-backup" ''
    set -euo pipefail

    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${npmPrefix}"
    export OPENCLAW_NIX_MODE=1

    readonly BACKUP_DIR="${backupDirectory}"
    readonly OPENCLAW_BIN="${npmPrefix}/bin/openclaw"

    mkdir -p "$BACKUP_DIR"

    readonly BACKUP_FILE="$BACKUP_DIR/openclaw-backup-$(date +%Y%m%d-%H%M%S).tar.gz"

    "$OPENCLAW_BIN" backup create --output "$BACKUP_FILE"

    ls -t "$BACKUP_DIR"/openclaw-backup-*.tar.gz 2>/dev/null | tail -n +${
      toString (maximumBackupsToKeep + 1)
    } | xargs -r rm
  '';
in
{
  options.openclaw.scheduledBackup = {
    enable = lib.mkEnableOption "daily scheduled backup for OpenClaw data";
  };

  config = lib.mkIf (cfg.enable && openclaw.gatewayService.enable) {
    systemd.user.services.openclaw-scheduled-backup = {
      Unit = {
        Description = "OpenClaw daily scheduled backup";
        After = [ "openclaw-gateway.service" ];
      };
      Service = {
        Type = "oneshot";
        ExecStart = "${scheduledBackupScript}";
      };
    };

    systemd.user.timers.openclaw-scheduled-backup = {
      Unit.Description = "OpenClaw scheduled backup timer";
      Timer = {
        OnCalendar = "*-*-* 03:00:00";
        Persistent = true;
      };
      Install.WantedBy = [ "timers.target" ];
    };
  };
}
