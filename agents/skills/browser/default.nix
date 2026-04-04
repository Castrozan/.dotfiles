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

    if ! "$MCP_BINARY" --version >/dev/null 2>&1; then
      echo "chrome-devtools-mcp binary not found at $MCP_BINARY" >&2
      exit 1
    fi

    exec "$MCP_BINARY" \
      --autoConnect \
      --userDataDir "${chromeGlobalUserDataDir}" \
      --usageStatistics false \
      "$@"
  '';
in
{
  mcpServerCommand = "${chromeDevtoolsMcpAutoconnectWrapper}/bin/chrome-devtools-mcp-autoconnect";
  inherit (install) installChromeDevtoolsMcpViaNpm;

  packages = [ ];
}
