{
  pkgs,
  config,
  lib,
  latest,
  ...
}:
let
  nodejs = pkgs.nodejs_22;
  homeDir = config.home.homeDirectory;
  chromeUserDataDirectory = "${homeDir}/.config/google-chrome";
  chromeDevtoolsMcpVersion = "0.20.3";
  chromeDevtoolsMcpNpmPrefix = "${homeDir}/.local/share/chrome-devtools-mcp-npm";
  chromeDevtoolsMcpBinary = "${chromeDevtoolsMcpNpmPrefix}/bin/chrome-devtools-mcp";

  a2aMcpVersion = "1.0.0";
  a2aMcpNpmPrefix = "${homeDir}/.local/share/a2a-mcp-server-npm";
  a2aMcpBinary = "${a2aMcpNpmPrefix}/bin/a2a-mcp-server";

  installNpmPackageWithRetry =
    {
      name,
      version,
      prefix,
      packageJsonSubpath,
    }:
    pkgs.writeShellScript "install-${name}" ''
      set -euo pipefail
      export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
      export NPM_CONFIG_PREFIX="${prefix}"

      PACKAGE_JSON="${prefix}/lib/node_modules/${packageJsonSubpath}/package.json"

      if [ -f "$PACKAGE_JSON" ] && grep -q '"version": "${version}"' "$PACKAGE_JSON"; then
        exit 0
      fi

      install_npm_package() {
        ${nodejs}/bin/npm install -g "${name}@${version}" \
          --prefix "${prefix}" \
          --registry "https://registry.npmjs.org/" \
          --prefer-offline \
          --no-audit \
          --no-fund \
          2>&1
      }

      if ! OUTPUT=$(install_npm_package); then
        echo "npm install ${name}@${version} failed (attempt 1), retrying..." >&2
        sleep 2
        if ! OUTPUT=$(install_npm_package); then
          echo "npm install ${name}@${version} failed after retry: $OUTPUT" >&2
          exit 1
        fi
      fi
    '';

  installChromeDevtoolsMcpViaNpm = installNpmPackageWithRetry {
    name = "chrome-devtools-mcp";
    version = chromeDevtoolsMcpVersion;
    prefix = chromeDevtoolsMcpNpmPrefix;
    packageJsonSubpath = "chrome-devtools-mcp";
  };

  installA2aMcpViaNpm = installNpmPackageWithRetry {
    name = "a2a-mcp-server";
    version = a2aMcpVersion;
    prefix = a2aMcpNpmPrefix;
    packageJsonSubpath = "a2a-mcp-server";
  };

  autoAcceptChromeDebuggingDialog = pkgs.writeShellScript "auto-accept-chrome-debugging-dialog" ''
    HYPRCTL=$(command -v hyprctl 2>/dev/null || true)
    WTYPE=$(command -v wtype 2>/dev/null || true)

    if [ -z "$HYPRCTL" ] || [ -z "$WTYPE" ]; then
      exit 0
    fi

    if [ -z "''${HYPRLAND_INSTANCE_SIGNATURE:-}" ]; then
      exit 0
    fi

    sleep 2
    "$HYPRCTL" dispatch focuswindow class:google-chrome 2>/dev/null || true
    sleep 1
    "$WTYPE" -k Tab -k Return 2>/dev/null || true
  '';

  chromeDevtoolsMcpAutoconnectWrapper = pkgs.writeShellScriptBin "chrome-devtools-mcp-autoconnect" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"

    DEVTOOLS_PORT_FILE="${chromeUserDataDirectory}/DevToolsActivePort"

    if [ ! -f "$DEVTOOLS_PORT_FILE" ]; then
      echo "Chrome not running with remote debugging." >&2
      echo "Start Chrome and enable at chrome://inspect/#remote-debugging" >&2
      echo "Or verify enterprise policy RemoteDebuggingAllowed is deployed." >&2
      exit 1
    fi

    CHROME_PORT=$(head -1 "$DEVTOOLS_PORT_FILE")
    CHROME_WS_PATH=$(tail -1 "$DEVTOOLS_PORT_FILE")

    if [ -z "$CHROME_PORT" ] || [ -z "$CHROME_WS_PATH" ]; then
      echo "DevToolsActivePort file is malformed (port=$CHROME_PORT path=$CHROME_WS_PATH)" >&2
      exit 1
    fi

    CHROME_WS_URL="ws://127.0.0.1:''${CHROME_PORT}''${CHROME_WS_PATH}"

    if ! "${chromeDevtoolsMcpBinary}" --version >/dev/null 2>&1; then
      echo "chrome-devtools-mcp binary not found at ${chromeDevtoolsMcpBinary}" >&2
      echo "Run home-manager activation or: npm install -g chrome-devtools-mcp@${chromeDevtoolsMcpVersion} --prefix ${chromeDevtoolsMcpNpmPrefix}" >&2
      exit 1
    fi

    ${autoAcceptChromeDebuggingDialog} &

    exec "${chromeDevtoolsMcpBinary}" \
      --wsEndpoint "$CHROME_WS_URL" \
      --usageStatistics false \
      "$@"
  '';

  enableChromeRemoteDebuggingToggle = pkgs.writeShellScript "enable-chrome-remote-debugging" ''
    set -euo pipefail
    CHROME_LOCAL_STATE="${chromeUserDataDirectory}/Local State"

    if [ ! -f "$CHROME_LOCAL_STATE" ]; then
      mkdir -p "${chromeUserDataDirectory}"
      echo '{"devtools":{"remote_debugging":{"user-enabled":true}}}' > "$CHROME_LOCAL_STATE"
      exit 0
    fi

    CURRENT_VALUE=$(${pkgs.jq}/bin/jq -r '.devtools.remote_debugging["user-enabled"] // false' "$CHROME_LOCAL_STATE" 2>/dev/null || echo "false")

    if [ "$CURRENT_VALUE" != "true" ]; then
      ${pkgs.jq}/bin/jq '.devtools.remote_debugging["user-enabled"] = true' "$CHROME_LOCAL_STATE" | ${pkgs.moreutils}/bin/sponge "$CHROME_LOCAL_STATE"
    fi
  '';

  mcpServersToInject = builtins.toJSON {
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
    a2a = {
      command = "${nodejs}/bin/node";
      args = [ a2aMcpBinary ];
    };
  };

  injectMcpServersIntoClaudeConfig = pkgs.writeShellScript "inject-mcp-servers" ''
    set -euo pipefail
    CLAUDE_CONFIG="${homeDir}/.claude.json"
    SERVERS='${mcpServersToInject}'

    if [ ! -f "$CLAUDE_CONFIG" ]; then
      echo '{"mcpServers":{}}' > "$CLAUDE_CONFIG"
    fi

    ${pkgs.jq}/bin/jq --argjson servers "$SERVERS" '.mcpServers = (.mcpServers // {}) * $servers' "$CLAUDE_CONFIG" | ${pkgs.moreutils}/bin/sponge "$CLAUDE_CONFIG"
  '';
in
{
  home = {
    packages = [
      latest.google-chrome
      pkgs.wtype
    ];

    file.".config/google-chrome/policies/managed/chrome-remote-debugging.json".text = builtins.toJSON {
      RemoteDebuggingAllowed = true;
      DeveloperToolsAvailability = 0;
    };

    activation = {
      injectMcpServers = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${injectMcpServersIntoClaudeConfig}
      '';

      installChromeDevtoolsMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${installChromeDevtoolsMcpViaNpm}
      '';

      installA2aMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${installA2aMcpViaNpm}
      '';

      enableChromeRemoteDebugging = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${enableChromeRemoteDebuggingToggle}
      '';
    };
  };
}
