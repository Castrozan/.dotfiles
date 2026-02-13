{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  nodejs = pkgs.nodejs_22;
  prefix = "$HOME/.local/share/openclaw-npm";

  gatewayScript = pkgs.writeShellScript "openclaw-gateway" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${prefix}"

    OPENCLAW_BIN="${prefix}/bin/openclaw"
    if [ ! -x "$OPENCLAW_BIN" ]; then
      echo "OpenClaw not installed yet. Run 'openclaw --version' first to trigger auto-install."
      exit 1
    fi

    exec "$OPENCLAW_BIN" gateway --port ${toString openclaw.gatewayPort}
  '';
in
{
  options.openclaw.gatewayService.enable = lib.mkEnableOption "OpenClaw gateway systemd user service";

  config = lib.mkIf openclaw.gatewayService.enable {
    systemd.user.services.openclaw-gateway = {
      Unit = {
        Description = "OpenClaw Gateway (port ${toString openclaw.gatewayPort})";
        After = [ "network.target" ];
      };

      Service = {
        Type = "simple";
        ExecStart = "${gatewayScript}";
        Restart = "on-failure";
        RestartSec = "10s";
        Environment = [
          "PATH=${nodejs}/bin:/usr/bin:/bin"
          "NODE_ENV=production"
          "OPENCLAW_NIX_MODE=1"
        ];
      };

      Install = {
        WantedBy = [ "default.target" ];
      };
    };
  };
}
