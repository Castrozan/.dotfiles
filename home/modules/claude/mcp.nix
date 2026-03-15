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
  chromeDevtoolsMcpVersion = "0.20.0";
  chromeDevtoolsMcpNpmPrefix = "${homeDir}/.local/share/chrome-devtools-mcp-npm";
  chromeDevtoolsMcpBinary = "${chromeDevtoolsMcpNpmPrefix}/bin/chrome-devtools-mcp";

  installChromeDevtoolsMcpViaNpm = pkgs.writeShellScript "install-chrome-devtools-mcp" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${chromeDevtoolsMcpNpmPrefix}"

    PACKAGE_JSON="${chromeDevtoolsMcpNpmPrefix}/lib/node_modules/chrome-devtools-mcp/package.json"

    if [ -f "$PACKAGE_JSON" ] && grep -q '"version": "${chromeDevtoolsMcpVersion}"' "$PACKAGE_JSON"; then
      exit 0
    fi

    ${nodejs}/bin/npm install -g "chrome-devtools-mcp@${chromeDevtoolsMcpVersion}" \
      --prefix "${chromeDevtoolsMcpNpmPrefix}" \
      --registry "https://registry.npmjs.org/"
  '';

  chromeDevtoolsMcpAutoconnectWrapper = pkgs.writeShellScriptBin "chrome-devtools-mcp-autoconnect" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"

    DEVTOOLS_PORT_FILE="${chromeUserDataDirectory}/DevToolsActivePort"

    if [ ! -f "$DEVTOOLS_PORT_FILE" ]; then
      echo "Chrome not running with remote debugging. Enable at chrome://inspect/#remote-debugging" >&2
      exit 1
    fi

    CHROME_PORT=$(head -1 "$DEVTOOLS_PORT_FILE")
    CHROME_WS_PATH=$(tail -1 "$DEVTOOLS_PORT_FILE")
    CHROME_WS_URL="ws://127.0.0.1:''${CHROME_PORT}''${CHROME_WS_PATH}"

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
      ${pkgs.moreutils}/bin/sponge <(${pkgs.jq}/bin/jq '.devtools.remote_debugging["user-enabled"] = true' "$CHROME_LOCAL_STATE") "$CHROME_LOCAL_STATE"
    fi
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

  home.file.".config/google-chrome/policies/managed/agent-browser-control.json".text =
    builtins.toJSON
      {
        RemoteDebuggingAllowed = true;
        DeveloperToolsAvailability = 0;
      };

  home.activation.installChromeDevtoolsMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${installChromeDevtoolsMcpViaNpm}
  '';

  home.activation.enableChromeRemoteDebugging = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${enableChromeRemoteDebuggingToggle}
  '';
}
