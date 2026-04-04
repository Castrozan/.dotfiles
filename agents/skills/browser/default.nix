{
  pkgs,
  homeDir,
  nodejs,
  chromePackage,
}:
let
  chromeDevtoolsMcpNpmPrefix = "${homeDir}/.local/share/chrome-devtools-mcp-npm";
  chromeDevtoolsMcpBinary = "${chromeDevtoolsMcpNpmPrefix}/bin/chrome-devtools-mcp";
  chromeGlobalUserDataDir = "${homeDir}/.config/chrome-global";
  devToolsActivePortFile = "${chromeGlobalUserDataDir}/DevToolsActivePort";
  chromeBinary = "${chromePackage}/bin/google-chrome-stable";
  maxWaitForChromeSeconds = 30;

  install = import ./install.nix {
    inherit
      pkgs
      nodejs
      chromeDevtoolsMcpNpmPrefix
      ;
  };

  chromeDevtoolsMcpAutoconnectWrapper = pkgs.writeShellScriptBin "chrome-devtools-mcp-autoconnect" ''
    set -euo pipefail

    readonly MCP_BINARY="${chromeDevtoolsMcpBinary}"
    readonly CHROME_BINARY="${chromeBinary}"
    readonly CHROME_USER_DATA_DIR="${chromeGlobalUserDataDir}"
    readonly DEVTOOLS_ACTIVE_PORT_FILE="${devToolsActivePortFile}"
    readonly MAX_WAIT=${toString maxWaitForChromeSeconds}

    _check_mcp_binary_exists() {
      if ! "$MCP_BINARY" --version >/dev/null 2>&1; then
        echo "chrome-devtools-mcp binary not found at $MCP_BINARY" >&2
        exit 1
      fi
    }

    _devtools_port_is_listening() {
      local port
      port=$(head -1 "$DEVTOOLS_ACTIVE_PORT_FILE" 2>/dev/null || echo "")
      [[ -n "$port" ]] && bash -c "echo >/dev/tcp/127.0.0.1/$port" 2>/dev/null
    }

    _chrome_is_ready() {
      [[ -f "$DEVTOOLS_ACTIVE_PORT_FILE" ]] && _devtools_port_is_listening
    }

    _remove_stale_devtools_active_port_file() {
      if [[ -f "$DEVTOOLS_ACTIVE_PORT_FILE" ]] && ! _devtools_port_is_listening; then
        rm -f "$DEVTOOLS_ACTIVE_PORT_FILE"
      fi
    }

    _launch_chrome_in_background() {
      echo "Launching Chrome Global..." >&2
      "$CHROME_BINARY" \
        --user-data-dir="$CHROME_USER_DATA_DIR" \
        --class=chrome-global \
        --remote-debugging-port=0 \
        --enable-features=UseNativeNotifications,WebRTCPipeWireCapturer \
        >/dev/null 2>&1 &
      disown
    }

    _wait_for_chrome_devtools_port() {
      for _attempt in $(seq 1 "$MAX_WAIT"); do
        if _chrome_is_ready; then
          return 0
        fi
        sleep 1
      done
      echo "Chrome DevToolsActivePort not available after ''${MAX_WAIT}s" >&2
      return 1
    }

    _ensure_chrome_is_running() {
      _remove_stale_devtools_active_port_file

      if _chrome_is_ready; then
        return 0
      fi

      _launch_chrome_in_background
      _wait_for_chrome_devtools_port
    }

    _check_mcp_binary_exists
    _ensure_chrome_is_running

    readonly DEVTOOLS_PORT=$(head -1 "$DEVTOOLS_ACTIVE_PORT_FILE")
    readonly DEVTOOLS_PATH=$(sed -n '2p' "$DEVTOOLS_ACTIVE_PORT_FILE")

    exec "$MCP_BINARY" \
      --wsEndpoint "ws://127.0.0.1:''${DEVTOOLS_PORT}''${DEVTOOLS_PATH}" \
      --usageStatistics false \
      "$@"
  '';
in
{
  mcpServerCommand = "${chromeDevtoolsMcpAutoconnectWrapper}/bin/chrome-devtools-mcp-autoconnect";
  inherit (install) installChromeDevtoolsMcpViaNpm;

  packages = [ ];
}
