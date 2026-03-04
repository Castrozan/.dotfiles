{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  cfg = openclaw.restartWatcher;
  nodejs = pkgs.nodejs_22;
  npmPrefix = "$HOME/.local/share/openclaw-npm";
  curl = "${pkgs.curl}/bin/curl";
  systemctl = "systemctl";

  restartWatcherScript = pkgs.writeShellScript "openclaw-restart-watcher" (
    ''
      set -Eeuo pipefail

      export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
      export NPM_CONFIG_PREFIX="${npmPrefix}"
      export OPENCLAW_NIX_MODE=1

      readonly OPENCLAW_BIN="${npmPrefix}/bin/openclaw"
      readonly GATEWAY_SERVICE="openclaw-gateway.service"
      readonly GATEWAY_PORT="${toString openclaw.gatewayPort}"
      readonly HEALTH_POLL_INTERVAL_SECONDS=${toString cfg.healthPollIntervalSeconds}
      readonly HEALTH_POLL_MAX_ATTEMPTS=${toString cfg.healthPollMaxAttempts}
      readonly POLL_INTERVAL_SECONDS=${toString cfg.pollIntervalSeconds}
      readonly SYSTEM_EVENT_TEXT="Gateway restarted after SIGUSR1. Check HEARTBEAT.md for interrupted tasks and resume any active entries you find."
      readonly CURL_BIN="${curl}"
      readonly SYSTEMCTL_CMD="${systemctl}"

    ''
    + builtins.readFile ./restart-watcher/log.sh
    + builtins.readFile ./restart-watcher/health-check.sh
    + builtins.readFile ./restart-watcher/gateway-service.sh
    + builtins.readFile ./restart-watcher/resume-event.sh
    + builtins.readFile ./restart-watcher/watch-loop.sh
    + ''

      main
    ''
  );
in
{
  options.openclaw.restartWatcher = {
    enable = lib.mkEnableOption "restart watcher that triggers agent task resumption after gateway restart";

    pollIntervalSeconds = lib.mkOption {
      type = lib.types.int;
      default = 3;
      description = "How often to check if gateway restarted (seconds)";
    };

    healthPollIntervalSeconds = lib.mkOption {
      type = lib.types.int;
      default = 2;
      description = "Interval between health checks while waiting for gateway to come back (seconds)";
    };

    healthPollMaxAttempts = lib.mkOption {
      type = lib.types.int;
      default = 30;
      description = "Maximum health check attempts before giving up on a restart";
    };
  };

  config = lib.mkIf (cfg.enable && openclaw.gatewayService.enable) {
    systemd.user.services.openclaw-restart-watcher = {
      Unit = {
        Description = "OpenClaw restart watcher — triggers agent task resumption after gateway restart";
        After = [ "openclaw-gateway.service" ];
        Wants = [ "openclaw-gateway.service" ];
      };

      Service = {
        Type = "simple";
        ExecStart = "${restartWatcherScript}";
        Restart = "always";
        RestartSec = "5s";
      };

      Install = {
        WantedBy = [ "default.target" ];
      };
    };
  };
}
