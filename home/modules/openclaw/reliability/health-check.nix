{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  cfg = openclaw.healthCheck;
  nodejs = pkgs.nodejs_22;
  npmPrefix = "$HOME/.local/share/openclaw-npm";
  jq = "${pkgs.jq}/bin/jq";
  systemctl = "systemctl";

  healthCheckScript = pkgs.writeShellScript "openclaw-health-check" ''
    set -euo pipefail

    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${npmPrefix}"
    export OPENCLAW_NIX_MODE=1

    readonly OPENCLAW_BIN="${npmPrefix}/bin/openclaw"
    readonly GATEWAY_SERVICE="openclaw-gateway.service"
    readonly GRACE_PERIOD_SECONDS=${toString cfg.gracePeriodSeconds}

    _log() {
      echo "[health-check] $*"
    }

    _gateway_is_active() {
      ${systemctl} --user is-active --quiet "$GATEWAY_SERVICE"
    }

    _gateway_uptime_seconds() {
      local active_enter_timestamp
      active_enter_timestamp=$(${systemctl} --user show "$GATEWAY_SERVICE" --property=ActiveEnterTimestamp --value)
      if [ -z "$active_enter_timestamp" ]; then
        echo "0"
        return
      fi
      local active_epoch
      active_epoch=$(date -d "$active_enter_timestamp" +%s 2>/dev/null || echo "0")
      local now_epoch
      now_epoch=$(date +%s)
      echo $(( now_epoch - active_epoch ))
    }

    _restart_gateway() {
      _log "restarting $GATEWAY_SERVICE"
      ${systemctl} --user restart "$GATEWAY_SERVICE"
    }

    _check_health_json() {
      "$OPENCLAW_BIN" health --json --timeout ${toString (cfg.probeTimeoutSeconds * 1000)} 2>/dev/null
    }

    _validate_gateway_health() {
      local health_json="$1"
      local gateway_ok
      gateway_ok=$(echo "$health_json" | ${jq} -r '.ok // false')
      if [ "$gateway_ok" != "true" ]; then
        _log "UNHEALTHY: gateway ok=$gateway_ok"
        return 1
      fi
      return 0
    }

    _validate_channel_accounts_healthy() {
      local health_json="$1"
      local channel_name="$2"

      local unhealthy_accounts
      unhealthy_accounts=$(echo "$health_json" | ${jq} -r --arg ch "$channel_name" '
        .channels[$ch].accounts // {} | to_entries
        | map(select(.value.probe.ok != true))
        | map(.key)
        | join(", ")
      ' 2>/dev/null || echo "")

      if [ -n "$unhealthy_accounts" ]; then
        _log "UNHEALTHY: $channel_name accounts failed probe: $unhealthy_accounts"
        return 1
      fi
      return 0
    }

    main() {
      if ! _gateway_is_active; then
        _log "gateway not active, skipping health check"
        exit 0
      fi

      local uptime_seconds
      uptime_seconds=$(_gateway_uptime_seconds)
      if [ "$uptime_seconds" -lt "$GRACE_PERIOD_SECONDS" ]; then
        _log "gateway uptime ''${uptime_seconds}s < grace period ''${GRACE_PERIOD_SECONDS}s, skipping"
        exit 0
      fi

      local health_json
      if ! health_json=$(_check_health_json); then
        _log "UNHEALTHY: failed to fetch health from gateway"
        _restart_gateway
        exit 0
      fi

      local is_healthy=true

      if ! _validate_gateway_health "$health_json"; then
        is_healthy=false
      fi

      local channel_name
      for channel_name in $(echo "$health_json" | ${jq} -r '.channelOrder[]' 2>/dev/null); do
        if ! _validate_channel_accounts_healthy "$health_json" "$channel_name"; then
          is_healthy=false
        fi
      done

      if [ "$is_healthy" = false ]; then
        _restart_gateway
      else
        _log "all agents healthy"
      fi
    }

    main
  '';
in
{
  options.openclaw.healthCheck = {
    enable = lib.mkEnableOption "periodic health check for OpenClaw gateway and agent channels";

    interval = lib.mkOption {
      type = lib.types.str;
      default = "2min";
      description = "Systemd timer interval between health checks";
    };

    gracePeriodSeconds = lib.mkOption {
      type = lib.types.int;
      default = 90;
      description = "Seconds after gateway start before health checks begin (allows channels to connect)";
    };

    probeTimeoutSeconds = lib.mkOption {
      type = lib.types.int;
      default = 15;
      description = "Timeout in seconds for the openclaw health probe";
    };
  };

  config = lib.mkIf (cfg.enable && openclaw.gatewayService.enable) {
    systemd.user.services.openclaw-health-check = {
      Unit = {
        Description = "OpenClaw gateway and agent channel health check";
        After = [ "openclaw-gateway.service" ];
      };
      Service = {
        Type = "oneshot";
        ExecStart = "${healthCheckScript}";
      };
    };

    systemd.user.timers.openclaw-health-check = {
      Unit.Description = "OpenClaw health check timer";
      Timer = {
        OnBootSec = "3min";
        OnUnitActiveSec = cfg.interval;
      };
      Install.WantedBy = [ "timers.target" ];
    };
  };
}
