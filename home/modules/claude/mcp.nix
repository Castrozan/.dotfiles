{
  pkgs,
  config,
  latest,
  ...
}:
let
  chromeDevtoolsMcp = pkgs.callPackage ../browser/chrome-devtools-mcp-package.nix { };
  homeDir = config.home.homeDirectory;
  chromeUserDataDirectory = "${homeDir}/.config/google-chrome";

  chromeDevtoolsMcpAutoconnectWrapper = pkgs.writeShellScriptBin "chrome-devtools-mcp-autoconnect" ''
    set -euo pipefail
    DEVTOOLS_PORT_FILE="${chromeUserDataDirectory}/DevToolsActivePort"

    if [ ! -f "$DEVTOOLS_PORT_FILE" ]; then
      echo "Chrome not running with remote debugging. Enable at chrome://inspect/#remote-debugging" >&2
      exit 1
    fi

    CHROME_PORT=$(head -1 "$DEVTOOLS_PORT_FILE")
    CHROME_WS_PATH=$(tail -1 "$DEVTOOLS_PORT_FILE")

    exec ${chromeDevtoolsMcp}/bin/chrome-devtools-mcp \
      --wsEndpoint "ws://127.0.0.1:''${CHROME_PORT}''${CHROME_WS_PATH}" \
      --usageStatistics false \
      "$@"
  '';

  mcpConfig = {
    mcpServers = {
      chrome-devtools = {
        command = "${chromeDevtoolsMcpAutoconnectWrapper}/bin/chrome-devtools-mcp-autoconnect";
        args = [ ];
      };
      scrapling-fetch = {
        command = "${homeDir}/.local/bin/scrapling-mcp";
        args = [ ];
      };
      codex = {
        command = "${homeDir}/.local/bin/codex";
        args = [ "mcp-server" ];
      };
    };
  };
in
{
  home.packages = [ latest.google-chrome ];
  home.file.".claude/mcp.json".text = builtins.toJSON mcpConfig;
}
