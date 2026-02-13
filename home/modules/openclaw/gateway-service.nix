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

  fixSessionPathsScript = pkgs.writeShellScript "openclaw-fix-session-paths" ''
    set -euo pipefail
    for sessionsJson in "$HOME"/.openclaw/agents/*/sessions/sessions.json; do
      [ -f "$sessionsJson" ] || continue
      if ${pkgs.gnugrep}/bin/grep -q '"sessionFile"' "$sessionsJson" 2>/dev/null; then
        ${pkgs.jq}/bin/jq 'walk(if type == "object" and .sessionFile then .sessionFile |= split("/")[-1] else . end)' \
          "$sessionsJson" | ${pkgs.moreutils}/bin/sponge "$sessionsJson"
      fi
    done
  '';

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
        ExecStartPre = "${fixSessionPathsScript}";
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
