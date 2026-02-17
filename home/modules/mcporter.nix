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
# chrome-devtools with --isolated so it doesn't collide with Claude Code's
# own chromium instance (both use the same chrome-profile directory).
{ pkgs, config, ... }:
let
  nodejs = pkgs.nodejs_22;
  mcporterNpmPrefix = "$HOME/.local/share/mcporter-npm";

  mcporterServerConfig = {
    mcpServers = {
      chrome-devtools = {
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
  home.packages = [ nodejs ];

  home.file.".mcporter/mcporter.json".text = builtins.toJSON mcporterServerConfig;

  home.activation.installMcporterViaNpm = config.lib.dag.entryAfter [ "writeBoundary" ] ''
    run ${installMcporterViaNpm}
  '';

  home.sessionPath = [ "${mcporterNpmPrefix}/bin" ];
}
