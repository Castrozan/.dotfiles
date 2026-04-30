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

  chromeDevtoolsStreamableHttpPort = 8767;
  chromeDevtoolsStreamableHttpSessionTimeoutMilliseconds = 300000;

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

  chromeDevtoolsStreamableHttpBridgeWrapper = pkgs.writeShellScriptBin "chrome-devtools-mcp-streamable-http-bridge" ''
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
      --outputTransport streamableHttp \
      --stateful \
      --sessionTimeout ${toString chromeDevtoolsStreamableHttpSessionTimeoutMilliseconds} \
      --port ${toString chromeDevtoolsStreamableHttpPort}
  '';
in
{
  mcpServerStreamableHttpUrl = "http://localhost:${toString chromeDevtoolsStreamableHttpPort}/mcp";
  streamableHttpBridgeCommand = "${chromeDevtoolsStreamableHttpBridgeWrapper}/bin/chrome-devtools-mcp-streamable-http-bridge";
  inherit (install) installChromeDevtoolsMcpViaNpm installSupergatewayViaNpm;
  inherit supergatewayBinary;

  packages = [ ];
}
