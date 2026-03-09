{ pkgs, config, ... }:
let
  nodejs = pkgs.nodejs_22;
  chromeDevtoolsMcp = pkgs.callPackage ../browser/chrome-devtools-mcp-package.nix { };
  mcporterNpmPrefix = "$HOME/.local/share/mcporter-npm";

  chromeDevtoolsWithCdpDiscovery = pkgs.writeShellScript "chrome-devtools-mcp-discover-cdp" ''
    set -euo pipefail
    CHROME_CDP_PORT=$(ss -tlnp 2>/dev/null \
      | grep -E 'chromium|chrome|brave' \
      | grep -o '127\.0\.0\.1:[0-9]*' \
      | head -1 \
      | cut -d: -f2)

    if [ -z "''${CHROME_CDP_PORT:-}" ]; then
      echo "no Chrome CDP port found — is pinchtab running?" >&2
      exit 1
    fi

    exec ${chromeDevtoolsMcp}/bin/chrome-devtools-mcp \
      --browserUrl="http://127.0.0.1:''${CHROME_CDP_PORT}" \
      --usageStatistics false
  '';

  scraplingMcp = pkgs.writeShellScript "scrapling-mcp" ''
    export PLAYWRIGHT_BROWSERS_PATH="$HOME/.local/share/scrapling-browsers"
    exec "$HOME/.local/share/scrapling-venv/bin/python" -m scrapling_fetch_mcp.mcp "$@"
  '';

  mcporterServerConfig = {
    mcpServers = {
      chrome-devtools = {
        command = "${chromeDevtoolsWithCdpDiscovery}";
        args = [ ];
      };
      chrome-devtools-isolated = {
        command = "${chromeDevtoolsMcp}/bin/chrome-devtools-mcp";
        args = [
          "--headless"
          "--executablePath"
          "${pkgs.chromium}/bin/chromium"
          "--usageStatistics"
          "false"
          "--isolated"
        ];
      };
      scrapling-fetch = {
        command = "${scraplingMcp}";
        args = [ ];
      };
    };
  };

  mcporterWrapper = pkgs.writeShellScriptBin "mcporter" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    exec "${mcporterNpmPrefix}/lib/node_modules/mcporter/dist/cli.js" "$@"
  '';

  installMcporterViaNpm = pkgs.writeShellScript "mcporter-install" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${mcporterNpmPrefix}"
    BIN="${mcporterNpmPrefix}/bin/mcporter"

    if [ -x "$BIN" ]; then
      exit 0
    fi

    ${nodejs}/bin/npm install -g "mcporter@latest" \
      --prefix "${mcporterNpmPrefix}" --no-audit --no-fund --loglevel=error
  '';
in
{
  home = {
    packages = [
      nodejs
      mcporterWrapper
    ];

    file.".mcporter/mcporter.json".text = builtins.toJSON mcporterServerConfig;

    activation.installMcporterViaNpm = config.lib.dag.entryAfter [ "writeBoundary" ] ''
      run ${installMcporterViaNpm}
    '';
  };
}
