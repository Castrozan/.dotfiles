{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  inherit (config.home) homeDirectory username;
  homeDir = homeDirectory;
  nodejs = pkgs.nodejs_22;
  prefix = "$HOME/.local/share/openclaw-npm";

  nixSystemPaths = lib.concatStringsSep ":" [
    "${nodejs}/bin"
    "${pkgs.git}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${username}/bin"
    "${homeDir}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

  secretsDirectory = "${homeDir}/.secrets";

  patchFastmcpStatelessHttpBeforeGatewayStart = pkgs.writeShellScript "patch-fastmcp-before-gateway" ''
    set -euo pipefail
    patchCount=0
    while IFS= read -r mcpPy; do
      if ${pkgs.gnugrep}/bin/grep -q 'stateless_http=True' "$mcpPy" 2>/dev/null; then
        ${pkgs.gnused}/bin/sed -i 's/FastMCP("hindsight-mcp-server", stateless_http=True)/FastMCP("hindsight-mcp-server")/' "$mcpPy"
        patchCount=$((patchCount + 1))
      fi
    done < <(${pkgs.findutils}/bin/find "${homeDir}/.cache/uv" -name "mcp.py" -path "*hindsight_api/api*" 2>/dev/null)
    if [ "$patchCount" -gt 0 ]; then
      echo "[gateway-pre] Patched FastMCP stateless_http kwarg in $patchCount file(s)"
    fi
  '';

  gatewayScript = pkgs.writeShellScript "openclaw-gateway" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${prefix}"

    if [ -f "${secretsDirectory}/gemini-api-key" ]; then
      GEMINI_API_KEY="$(cat "${secretsDirectory}/gemini-api-key")"
      export GEMINI_API_KEY
    fi

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
        ExecStartPre = "${patchFastmcpStatelessHttpBeforeGatewayStart}";
        ExecStart = "${gatewayScript}";
        Restart = "always";
        RestartSec = "5s";
        CPUQuota = "150%";
        MemoryMax = "2G";
        OOMScoreAdjust = -500;
        Environment = [
          "PATH=${nixSystemPaths}"
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
