{
  pkgs,
  homeDir,
  nodejs,
}:
let
  chromeDevtoolsMcpNpmPrefix = "${homeDir}/.local/share/chrome-devtools-mcp-npm";
  chromeDevtoolsMcpBinary = "${chromeDevtoolsMcpNpmPrefix}/bin/chrome-devtools-mcp";
  devToolsActivePortFile = "${homeDir}/.config/google-chrome/DevToolsActivePort";

  install = import ./install.nix {
    inherit
      pkgs
      homeDir
      nodejs
      chromeDevtoolsMcpNpmPrefix
      ;
  };

  acceptCdpConsentDialogScript = ./scripts/accept_cdp_consent_dialog.py;

  chromeDevtoolsMcpAutoconnectWrapper = pkgs.writeShellScriptBin "chrome-devtools-mcp-autoconnect" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:${pkgs.ydotool}/bin:${pkgs.python312}/bin:''${PATH:+:$PATH}"

    readonly DEVTOOLS_ACTIVE_PORT_FILE="${devToolsActivePortFile}"
    readonly MCP_BINARY="${chromeDevtoolsMcpBinary}"
    readonly CONSENT_ACCEPTOR="${acceptCdpConsentDialogScript}"
    readonly MAX_WAIT_FOR_CHROME_SECONDS=60

    _check_mcp_binary_exists() {
      if ! "$MCP_BINARY" --version >/dev/null 2>&1; then
        echo "chrome-devtools-mcp binary not found at $MCP_BINARY" >&2
        exit 1
      fi
    }

    _debugging_port_is_listening() {
      local port
      port=$(head -1 "$DEVTOOLS_ACTIVE_PORT_FILE" 2>/dev/null || echo "")
      [[ -n "$port" ]] && bash -c "echo >/dev/tcp/127.0.0.1/$port" 2>/dev/null
    }

    _remove_stale_devtools_active_port_file() {
      if [[ -f "$DEVTOOLS_ACTIVE_PORT_FILE" ]] && ! _debugging_port_is_listening; then
        rm -f "$DEVTOOLS_ACTIVE_PORT_FILE"
      fi
    }

    _wait_for_chrome() {
      _remove_stale_devtools_active_port_file

      if [[ -f "$DEVTOOLS_ACTIVE_PORT_FILE" ]] && _debugging_port_is_listening; then
        return 0
      fi

      echo "Waiting for Chrome (launch it manually)..." >&2
      for _attempt in $(seq 1 "$MAX_WAIT_FOR_CHROME_SECONDS"); do
        _remove_stale_devtools_active_port_file
        if [[ -f "$DEVTOOLS_ACTIVE_PORT_FILE" ]] && _debugging_port_is_listening; then
          return 0
        fi
        sleep 1
      done

      echo "Chrome not detected after ''${MAX_WAIT_FOR_CHROME_SECONDS}s" >&2
      exit 1
    }

    _build_websocket_endpoint_from_devtools_active_port() {
      local port ws_path
      port=$(sed -n '1p' "$DEVTOOLS_ACTIVE_PORT_FILE")
      ws_path=$(sed -n '2p' "$DEVTOOLS_ACTIVE_PORT_FILE")
      echo "ws://127.0.0.1:''${port}''${ws_path}"
    }

    _launch_consent_dialog_acceptor_in_background() {
      python3 "$CONSENT_ACCEPTOR" &
      disown
    }

    _check_mcp_binary_exists
    _wait_for_chrome

    readonly WS_ENDPOINT=$(_build_websocket_endpoint_from_devtools_active_port)
    echo "Connecting to Chrome at $WS_ENDPOINT" >&2

    _launch_consent_dialog_acceptor_in_background

    exec "$MCP_BINARY" \
      --wsEndpoint "$WS_ENDPOINT" \
      --usageStatistics false \
      "$@"
  '';
in
{
  mcpServerCommand = "${chromeDevtoolsMcpAutoconnectWrapper}/bin/chrome-devtools-mcp-autoconnect";
  inherit (install) installChromeDevtoolsMcpViaNpm;

  packages = [ ];
}
