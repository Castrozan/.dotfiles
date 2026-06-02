{
  pkgs,
  homeDir,
  nodejs,
  chromePackage,
}:
let
  inherit (pkgs.stdenv.hostPlatform) isDarwin;
  chromeDevtoolsMcpPackage = import ./chrome-devtools-mcp-package.nix {
    inherit pkgs nodejs;
  };
  chromeDevtoolsMcpBinary = "${chromeDevtoolsMcpPackage}/bin/chrome-devtools-mcp";
  chromeGlobalUserDataDir =
    if isDarwin then
      "${homeDir}/Library/Application Support/Google/Chrome"
    else
      "${homeDir}/.config/chrome-global";

  supergatewayPackage = import ./supergateway-package.nix {
    inherit pkgs nodejs;
  };
  supergatewayBinary = "${supergatewayPackage}/bin/supergateway";

  chromeDevtoolsStreamableHttpPort = 8767;
  chromeDevtoolsStreamableHttpSessionTimeoutMilliseconds = 3600000;

  chromeDevtoolsMcpAutoconnectCommand = builtins.concatStringsSep " " [
    chromeDevtoolsMcpBinary
    "--autoConnect"
    "--userDataDir '${chromeGlobalUserDataDir}'"
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

  chromeDevtoolsMcpOrphanReaper = pkgs.writeShellScript "chrome-devtools-mcp-orphan-reaper" ''
    set -euo pipefail
    ${pkgs.procps}/bin/pkill -9 -f 'chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js' || true
  '';
in
{
  mcpServerStreamableHttpUrl = "http://localhost:${toString chromeDevtoolsStreamableHttpPort}/mcp";
  streamableHttpBridgeCommand = "${chromeDevtoolsStreamableHttpBridgeWrapper}/bin/chrome-devtools-mcp-streamable-http-bridge";
  inherit chromeDevtoolsMcpOrphanReaper;
  inherit supergatewayBinary;

  packages = [ ];
}
