{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  cfg = openclaw.timeoutRecovery;
  nodejs = pkgs.nodejs_22;
  npmPrefix = "$HOME/.local/share/openclaw-npm";

  timeoutRecoveryScript = pkgs.writeShellScript "openclaw-timeout-recovery" (
    ''
      set -Eeuo pipefail

      export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
      export NPM_CONFIG_PREFIX="${npmPrefix}"
      export OPENCLAW_NIX_MODE=1

      readonly OPENCLAW_BIN="${npmPrefix}/bin/openclaw"
      readonly GATEWAY_SERVICE="openclaw-gateway.service"
      readonly COOLDOWN_DIR="''${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/openclaw-timeout-recovery"
      readonly COOLDOWN_SECONDS=${toString cfg.cooldownSeconds}

    ''
    + builtins.readFile ../timeout-recovery/log.sh
    + builtins.readFile ../timeout-recovery/extract-agent-from-lane.sh
    + builtins.readFile ../timeout-recovery/session-cleanup.sh
    + builtins.readFile ../timeout-recovery/notify-user.sh
    + builtins.readFile ../timeout-recovery/watch-loop.sh
    + ''

      main
    ''
  );
in
{
  options.openclaw.timeoutRecovery = {
    enable = lib.mkEnableOption "timeout recovery monitor that detects LLM timeouts and auto-recovers";

    cooldownSeconds = lib.mkOption {
      type = lib.types.int;
      default = 300;
      description = "Minimum seconds between recovery actions for the same agent (prevents recovery loops)";
    };
  };

  config = lib.mkIf (cfg.enable && openclaw.gatewayService.enable) {
    systemd.user.services.openclaw-timeout-recovery = {
      Unit = {
        Description = "OpenClaw timeout recovery — detects LLM timeouts, cleans sessions, and notifies user";
        After = [ "openclaw-gateway.service" ];
        Wants = [ "openclaw-gateway.service" ];
      };

      Service = {
        Type = "simple";
        ExecStart = "${timeoutRecoveryScript}";
        Restart = "always";
        RestartSec = "10s";
      };

      Install = {
        WantedBy = [ "default.target" ];
      };
    };
  };
}
