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
# chrome-devtools to use the pw-browser persistent profile so agents get
# authenticated access to logged-in sites (GitHub, GitLab, Betha, Google).
{ pkgs, config, ... }:
let
  nodejs = pkgs.nodejs_22;
  mcporterNpmPrefix = "$HOME/.local/share/mcporter-npm";

  mcporterServerConfig = {
    mcpServers = {
      # Connects to pinchtab's Chrome instance (port 9222) for authenticated access.
      # Start the browser first: `pinchtab` (runs headless by default)
      # Falls back gracefully if browser isn't running.
      chrome-devtools = {
        command = "${nodejs}/bin/npx";
        args = [
          "chrome-devtools-mcp@latest"
          "--browser-url=http://127.0.0.1:9222"
          "--usageStatistics"
          "false"
        ];
      };
      # Standalone headless Chromium for when pw-browser isn't needed.
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
