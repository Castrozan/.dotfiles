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
  inherit (config.home) username;
  inherit (pkgs.stdenv.hostPlatform) isDarwin;
  chromeBinary =
    if isDarwin then
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    else
      "${latest.google-chrome}/bin/google-chrome-stable";

  browserMcp = import ../../../../agents/skills/browser/install {
    inherit
      pkgs
      nodejs
      homeDir
      ;
    chromePackage = latest.google-chrome;
  };

  browserUseConfigDir = "${homeDir}/.config/browseruse";

  browserUseMcpWrapper = pkgs.writeShellScript "browser-use-mcp" ''
    export BROWSER_USE_CONFIG_PATH="${browserUseConfigDir}/config.json"
    export ANONYMIZED_TELEMETRY=false
    exec ${pkgs.uv}/bin/uvx --from 'browser-use[cli]' browser-use --mcp "$@"
  '';

  browserUseMcpStreamableHttpPort = 8768;
  browserUseMcpStreamableHttpSessionTimeoutMilliseconds = 60000;

  browserUseMcpOrphanReaper = pkgs.writeShellScript "browser-use-mcp-orphan-reaper" ''
    set -euo pipefail
    ${pkgs.procps}/bin/pkill -9 -f 'browser-use --mcp' || true
  '';

  browserUseMcpStreamableHttpBridgeLauncher = pkgs.writeShellScript "browser-use-mcp-streamable-http-bridge-launcher" ''
    set -euo pipefail
    ${browserUseMcpOrphanReaper}

    if ! "${browserMcp.supergatewayBinary}" --version >/dev/null 2>&1; then
      echo "supergateway binary not found at ${browserMcp.supergatewayBinary}" >&2
      exit 1
    fi

    exec "${browserMcp.supergatewayBinary}" \
      --stdio "${browserUseMcpWrapper}" \
      --outputTransport streamableHttp \
      --stateful \
      --sessionTimeout ${toString browserUseMcpStreamableHttpSessionTimeoutMilliseconds} \
      --port ${toString browserUseMcpStreamableHttpPort}
  '';

  a2aMcp = import ../../agents/a2a/install.nix {
    inherit
      pkgs
      nodejs
      homeDir
      ;
  };

  nixSystemPaths = lib.concatStringsSep ":" [
    "${nodejs}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${username}/bin"
    "${homeDir}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

  crossPlatformMcpBridgeServiceSpecs = {
    browser-use-mcp-bridge = {
      description = "Browser-use MCP streamable HTTP bridge (supergateway)";
      launcher = browserUseMcpStreamableHttpBridgeLauncher;
      linuxOnlyServiceExtraConfig = {
        MemoryMax = "2G";
      };
    };
  };

  linuxOnlyMcpBridgeServiceSpecs = { };
in
{
  imports = [
    (import ./mcp-bridge-runners.nix {
      inherit
        homeDir
        nixSystemPaths
        crossPlatformMcpBridgeServiceSpecs
        linuxOnlyMcpBridgeServiceSpecs
        ;
    })
    (import ./browser-use-config-patcher.nix {
      inherit browserUseConfigDir chromeBinary;
    })
    (import ./inject-mcp-servers-into-claude-config.nix {
      inherit homeDir;
      inherit (browserMcp) chromeDevtoolsMcpStdioCommand chromeDevtoolsMcpStdioArgs;
      a2aMcpStdioCommand = a2aMcp.mcpServerCommand;
      a2aMcpStdioArgs = a2aMcp.mcpServerArgs;
      inherit browserUseMcpStreamableHttpPort;
      codexBinaryPath = "${homeDir}/.local/bin/codex";
    })
  ];

  home = {
    inherit (browserMcp) packages;
  };
}
