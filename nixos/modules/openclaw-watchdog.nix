{
  config,
  lib,
  pkgs,
  ...
}:

with lib;

let
  cfg = config.services.openclaw-watchdog;
in
{
  options.services.openclaw-watchdog = {
    enable = mkEnableOption "OpenClaw gateway watchdog";

    interval = mkOption {
      type = types.int;
      default = 30;
      description = "Check interval in seconds";
    };

    gatewayPort = mkOption {
      type = types.int;
      default = 18789;
      description = "OpenClaw gateway port";
    };

    user = mkOption {
      type = types.str;
      default = "zanoni";
      description = "User running OpenClaw";
    };
  };

  config = mkIf cfg.enable {
    systemd.services.openclaw-watchdog = {
      description = "OpenClaw Gateway Watchdog";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];

      serviceConfig = {
        Type = "simple";
        User = cfg.user;
        Restart = "always";
        RestartSec = 10;
      };

      script = ''
        while true; do
          if ! ${pkgs.curl}/bin/curl -s -f http://localhost:${toString cfg.gatewayPort}/health > /dev/null 2>&1; then
            echo "[$(date -Iseconds)] Gateway down - running doctor fix..."
            
            # Run openclaw doctor --fix
            su ${cfg.user} -c 'openclaw doctor --fix' || echo "Doctor fix failed"
            
            # Restart gateway
            su ${cfg.user} -c 'openclaw gateway restart' || echo "Restart failed"
            
            echo "[$(date -Iseconds)] Recovery attempted"
          fi
          
          sleep ${toString cfg.interval}
        done
      '';
    };
  };
}
