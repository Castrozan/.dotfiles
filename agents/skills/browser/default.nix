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

  supergatewayNpmPrefix = "${homeDir}/.local/share/supergateway-npm";
  supergatewayBinary = "${supergatewayNpmPrefix}/bin/supergateway";

  chromeDevtoolsSsePort = 8767;

  install = import ./install.nix {
    inherit
      pkgs
      nodejs
      chromeDevtoolsMcpNpmPrefix
      supergatewayNpmPrefix
      ;
  };

  chromeDevtoolsMcpAutoconnectCommand = builtins.concatStringsSep " " [
    chromeDevtoolsMcpBinary
    "--autoConnect"
    "--userDataDir ${chromeGlobalUserDataDir}"
    "--usageStatistics false"
  ];

  chromeDevtoolsSseBridgeWrapper = pkgs.writeShellScriptBin "chrome-devtools-mcp-sse-bridge" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"

    if ! "${chromeDevtoolsMcpBinary}" --version >/dev/null 2>&1; then
      echo "chrome-devtools-mcp binary not found at ${chromeDevtoolsMcpBinary}" >&2
      exit 1
    fi

    if ! "${supergatewayBinary}" --version >/dev/null 2>&1; then
      echo "supergateway binary not found at ${supergatewayBinary}" >&2
      exit 1
    fi

    exec "${supergatewayBinary}" \
      --stdio "${chromeDevtoolsMcpAutoconnectCommand}" \
      --port ${toString chromeDevtoolsSsePort}
  '';
in
{
  mcpServerSseUrl = "http://localhost:${toString chromeDevtoolsSsePort}/sse";
  sseBridgeCommand = "${chromeDevtoolsSseBridgeWrapper}/bin/chrome-devtools-mcp-sse-bridge";
  inherit (install) installChromeDevtoolsMcpViaNpm installSupergatewayViaNpm;

  packages = [ ];
}
