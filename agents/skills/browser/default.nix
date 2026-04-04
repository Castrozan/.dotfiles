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
  chromeBinary = "${chromePackage}/bin/google-chrome-stable";
  devToolsActivePortFile = "${chromeGlobalUserDataDir}/DevToolsActivePort";

  install = import ./install.nix {
    inherit
      pkgs
      nodejs
      chromeDevtoolsMcpNpmPrefix
      ;
  };

  consentAcceptorScript = ./scripts/accept_cdp_consent_dialog.py;

  chromeDevtoolsMcpAutoconnectWrapper = pkgs.writeShellScriptBin "chrome-devtools-mcp-autoconnect" ''
    set -euo pipefail

    readonly MCP_BINARY="${chromeDevtoolsMcpBinary}"
    readonly CHROME_BINARY="${chromeBinary}"
    readonly CHROME_USER_DATA_DIR="${chromeGlobalUserDataDir}"
    readonly DEVTOOLS_ACTIVE_PORT_FILE="${devToolsActivePortFile}"

    _check_mcp_binary_exists() {
      if ! "$MCP_BINARY" --version >/dev/null 2>&1; then
        echo "chrome-devtools-mcp binary not found at $MCP_BINARY" >&2
        exit 1
      fi
    }

    _is_chrome_running() {
      ${pkgs.procps}/bin/pgrep -f "google-chrome.*chrome-global" >/dev/null 2>&1
    }

    _launch_chrome_bare() {
      echo "Launching Chrome Global (bare)..." >&2
      DISPLAY=''${DISPLAY:-:0} \
      WAYLAND_DISPLAY=''${WAYLAND_DISPLAY:-wayland-1} \
      XDG_RUNTIME_DIR=''${XDG_RUNTIME_DIR:-/run/user/$(id -u)} \
      "$CHROME_BINARY" \
        --user-data-dir="$CHROME_USER_DATA_DIR" \
        --class=chrome-global \
        --enable-features=UseNativeNotifications,WebRTCPipeWireCapturer \
        >/dev/null 2>&1 &
      disown
      sleep 3
    }

    _enable_remote_debugging_toggle() {
      echo "Opening chrome://inspect to enable remote debugging..." >&2
      "$CHROME_BINARY" \
        --user-data-dir="$CHROME_USER_DATA_DIR" \
        "chrome://inspect/#remote-debugging" \
        >/dev/null 2>&1 &
      disown
      sleep 2
    }

    _wait_for_devtools_active_port() {
      local max_wait=15
      for _attempt in $(seq 1 "$max_wait"); do
        if [ -f "$DEVTOOLS_ACTIVE_PORT_FILE" ]; then
          local port
          port=$(head -1 "$DEVTOOLS_ACTIVE_PORT_FILE" 2>/dev/null || echo "")
          if [ -n "$port" ] && bash -c "echo >/dev/tcp/127.0.0.1/$port" 2>/dev/null; then
            echo "DevTools port $port is listening" >&2
            return 0
          fi
        fi
        sleep 1
      done
      echo "DevToolsActivePort not available after ''${max_wait}s" >&2
      return 1
    }

    _accept_consent_dialog_in_background() {
      if [ -n "''${HYPRLAND_INSTANCE_SIGNATURE:-}" ]; then
        echo "Starting consent dialog acceptor..." >&2
        ${pkgs.python312}/bin/python3 ${consentAcceptorScript} &
      fi
    }

    _remove_stale_devtools_active_port() {
      if [ -f "$DEVTOOLS_ACTIVE_PORT_FILE" ]; then
        local port
        port=$(head -1 "$DEVTOOLS_ACTIVE_PORT_FILE" 2>/dev/null || echo "")
        if [ -z "$port" ] || ! bash -c "echo >/dev/tcp/127.0.0.1/$port" 2>/dev/null; then
          rm -f "$DEVTOOLS_ACTIVE_PORT_FILE"
        fi
      fi
    }

    _check_mcp_binary_exists
    _remove_stale_devtools_active_port

    if ! _is_chrome_running; then
      _launch_chrome_bare
    fi

    if [ ! -f "$DEVTOOLS_ACTIVE_PORT_FILE" ]; then
      _accept_consent_dialog_in_background
      _enable_remote_debugging_toggle
      _wait_for_devtools_active_port
    fi

    exec "$MCP_BINARY" \
      --autoConnect \
      --userDataDir "$CHROME_USER_DATA_DIR" \
      --usageStatistics false \
      "$@"
  '';
in
{
  mcpServerCommand = "${chromeDevtoolsMcpAutoconnectWrapper}/bin/chrome-devtools-mcp-autoconnect";
  inherit (install) installChromeDevtoolsMcpViaNpm;

  packages = [ ];
}
