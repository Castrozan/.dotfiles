{ pkgs, config }:
let
  chromeDevtoolsMcp = pkgs.callPackage ./chrome-devtools-mcp-package.nix { };
  homeDir = config.home.homeDirectory;
  chromeUserDataDirectory = "${homeDir}/.config/google-chrome";
in
pkgs.writeShellScriptBin "chrome-devtools-mcp-autoconnect" ''
  set -euo pipefail
  DEVTOOLS_ACTIVE_PORT_FILE="${chromeUserDataDirectory}/DevToolsActivePort"

  if [ ! -f "$DEVTOOLS_ACTIVE_PORT_FILE" ]; then
    echo "Chrome is not running with remote debugging enabled." >&2
    echo "Enable it at chrome://inspect/#remote-debugging" >&2
    exit 1
  fi

  CHROME_DEBUGGING_PORT=$(head -1 "$DEVTOOLS_ACTIVE_PORT_FILE")
  CHROME_DEBUGGING_WEBSOCKET_PATH=$(tail -1 "$DEVTOOLS_ACTIVE_PORT_FILE")
  CHROME_DEBUGGING_WEBSOCKET_URL="ws://127.0.0.1:''${CHROME_DEBUGGING_PORT}''${CHROME_DEBUGGING_WEBSOCKET_PATH}"

  exec ${chromeDevtoolsMcp}/bin/chrome-devtools-mcp \
    --wsEndpoint "$CHROME_DEBUGGING_WEBSOCKET_URL" \
    --usageStatistics false \
    "$@"
''
