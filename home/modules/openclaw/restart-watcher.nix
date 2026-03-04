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

  restartWatcherScript = pkgs.writeShellScript "openclaw-restart-watcher" ''
    set -Eeuo pipefail

    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${npmPrefix}"
    export OPENCLAW_NIX_MODE=1

    readonly OPENCLAW_BIN="${npmPrefix}/bin/openclaw"
    readonly GATEWAY_SERVICE="openclaw-gateway.service"
    readonly GATEWAY_PORT="${toString openclaw.gatewayPort}"
    readonly HEALTH_POLL_INTERVAL_SECONDS=${toString cfg.healthPollIntervalSeconds}
    readonly HEALTH_POLL_MAX_ATTEMPTS=${toString cfg.healthPollMaxAttempts}
    readonly SYSTEM_EVENT_TEXT="Gateway restarted after SIGUSR1. Check HEARTBEAT.md for interrupted tasks and resume any active entries you find."

    _log() {
      echo "[restart-watcher] $(date -Iseconds) $*"
    }

    _wait_for_gateway_healthy() {
      local attempt=0
      while [ "$attempt" -lt "$HEALTH_POLL_MAX_ATTEMPTS" ]; do
        if ${curl} -sf "http://localhost:''${GATEWAY_PORT}/health" > /dev/null 2>&1; then
          return 0
        fi
        attempt=$((attempt + 1))
        sleep "$HEALTH_POLL_INTERVAL_SECONDS"
      done
      return 1
    }

    _send_resume_event() {
      _log "sending system event to wake agents"
      "$OPENCLAW_BIN" system event \
        --mode now \
        --text "$SYSTEM_EVENT_TEXT" \
        --timeout 30000 2>&1 || _log "system event failed (gateway may not be ready)"
    }

    _handle_gateway_restart() {
      _log "gateway restart detected, waiting for healthy status"

      if _wait_for_gateway_healthy; then
        _log "gateway is healthy, triggering agent resume"
        _send_resume_event
      else
        _log "gateway did not become healthy after $HEALTH_POLL_MAX_ATTEMPTS attempts"
      fi
    }

    _get_gateway_active_enter_timestamp() {
      ${systemctl} --user show "$GATEWAY_SERVICE" \
        --property=ActiveEnterTimestamp --value 2>/dev/null || echo ""
    }

    _wait_for_gateway_service() {
      _log "waiting for $GATEWAY_SERVICE to become active"
      while true; do
        if ${systemctl} --user is-active "$GATEWAY_SERVICE" > /dev/null 2>&1; then
          _log "$GATEWAY_SERVICE is active"
          return 0
        fi
        sleep ${toString cfg.pollIntervalSeconds}
      done
    }

    _watch_for_restarts() {
      _log "watching $GATEWAY_SERVICE for restart events"

      _wait_for_gateway_service

      local previous_active_enter_timestamp=""
      previous_active_enter_timestamp=$(_get_gateway_active_enter_timestamp)

      while true; do
        sleep ${toString cfg.pollIntervalSeconds}

        local current_active_enter_timestamp
        current_active_enter_timestamp=$(_get_gateway_active_enter_timestamp)

        if [ -z "$current_active_enter_timestamp" ]; then
          _log "gateway is down, waiting for restart"
          previous_active_enter_timestamp=""
          continue
        fi

        if [ "$current_active_enter_timestamp" != "$previous_active_enter_timestamp" ] \
          && [ -n "$previous_active_enter_timestamp" ]; then
          _handle_gateway_restart
        elif [ -z "$previous_active_enter_timestamp" ] && [ -n "$current_active_enter_timestamp" ]; then
          _log "gateway came back up after being down"
          _handle_gateway_restart
        fi

        previous_active_enter_timestamp="$current_active_enter_timestamp"
      done
    }

    main() {
      _watch_for_restarts
    }

    main
  '';
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
