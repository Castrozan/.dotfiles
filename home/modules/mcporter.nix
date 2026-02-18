# mcporter — CLI bridge for MCP (Model Context Protocol) servers.
#
# Why mcporter instead of openclaw-mcp-adapter plugin?
# The adapter registers tools via api.registerTool() at the gateway runtime level.
# Only the default agent's session sees those tools — non-default agents (jenny,
# monster, silver) never receive them. This is a gateway core constraint, not a
# config issue. Both global tools.allow and per-agent tools.allow were tested and
# confirmed broken for non-default agents (openclaw#11832, adapter#6).
#
# mcporter solves this by enabling SKILL.md-based tool invocation: agents read
# skill docs from the system prompt and shell out via `mcporter call`. This works
# for ALL agents because skills are file-based, not runtime-registered.
#
# mcporter auto-imports servers from ~/.claude/mcp.json but we override
# chrome-devtools to connect to pinchtab's Chrome instance so agents get
# authenticated access to logged-in sites (GitHub, GitLab, Betha, Google).
{ pkgs, config, ... }:
let
  nodejs = pkgs.nodejs_22;
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

    exec ${nodejs}/bin/npx chrome-devtools-mcp@latest \
      --browser-url="http://127.0.0.1:''${CHROME_CDP_PORT}" \
      --usageStatistics false
  '';

  mcporterServerConfig = {
    mcpServers = {
      chrome-devtools = {
        command = "${chromeDevtoolsWithCdpDiscovery}";
        args = [ ];
      };
      chrome-devtools-isolated = {
        command = "${nodejs}/bin/npx";
        args = [
          "chrome-devtools-mcp@latest"
          "--headless"
          "--executablePath"
          "${pkgs.chromium}/bin/chromium"
          "--usageStatistics"
          "false"
          "--isolated"
        ];
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
      echo "[mcporter-install] Already installed, skipping"
      exit 0
    fi

    echo "[mcporter-install] Installing mcporter..."
    ${nodejs}/bin/npm install -g "mcporter@latest" \
      --prefix "${mcporterNpmPrefix}" --no-audit --no-fund --loglevel=error
    echo "[mcporter-install] Done"
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
