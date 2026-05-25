{
  pkgs,
  config,
  lib,
  latest,
  ...
}:
let
  inherit (pkgs.stdenv.hostPlatform) isLinux;
  nodejs = pkgs.nodejs_22;
  homeDir = config.home.homeDirectory;
  inherit (config.home) username;
  chromeBinary = "${latest.google-chrome}/bin/google-chrome-stable";

  browserMcp = import ../../../agents/skills/browser/install {
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
  browserUseMcpStreamableHttpSessionTimeoutMilliseconds = 300000;

  browserUseMcpStreamableHttpBridgeLauncher = pkgs.writeShellScript "browser-use-mcp-streamable-http-bridge-launcher" ''
    set -euo pipefail

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

  a2aMcp = import ./a2a-mcp-server/install {
    inherit
      pkgs
      nodejs
      homeDir
      ;
  };

  a2aMcpStreamableHttpPort = 8769;
  a2aMcpStreamableHttpSessionTimeoutMilliseconds = 300000;

  a2aMcpStreamableHttpBridgeLauncher = pkgs.writeShellScript "a2a-mcp-streamable-http-bridge-launcher" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"

    if ! "${browserMcp.supergatewayBinary}" --version >/dev/null 2>&1; then
      echo "supergateway binary not found at ${browserMcp.supergatewayBinary}" >&2
      exit 1
    fi

    exec "${browserMcp.supergatewayBinary}" \
      --stdio "${a2aMcp.mcpServerCommand} ${builtins.head a2aMcp.mcpServerArgs}" \
      --outputTransport streamableHttp \
      --stateful \
      --sessionTimeout ${toString a2aMcpStreamableHttpSessionTimeoutMilliseconds} \
      --port ${toString a2aMcpStreamableHttpPort}
  '';

  chromeDevtoolsMcpStreamableHttpBridgeLauncher = pkgs.writeShellScript "chrome-devtools-mcp-streamable-http-bridge-launcher" ''
    set -euo pipefail
    ${browserMcp.chromeDevtoolsMcpOrphanReaper}
    exec ${browserMcp.streamableHttpBridgeCommand}
  '';

  twitterCli = import ../../../agents/skills/comms/skills/twitter/install {
    inherit
      pkgs
      homeDir
      ;
  };

  mcpServersToInject = builtins.toJSON (
    {
      chrome-devtools = {
        type = "http";
        url = browserMcp.mcpServerStreamableHttpUrl;
      };
      codex = {
        command = "${homeDir}/.local/bin/codex";
        args = [ "mcp-server" ];
      };
      a2a = {
        type = "http";
        url = "http://localhost:${toString a2aMcpStreamableHttpPort}/mcp";
      };
    }
    // lib.optionalAttrs isLinux {
      browser-use = {
        type = "http";
        url = "http://localhost:${toString browserUseMcpStreamableHttpPort}/mcp";
      };
    }
  );

  injectMcpServersIntoClaudeConfig = pkgs.writeShellScript "inject-mcp-servers" ''
    set -euo pipefail
    CLAUDE_CONFIG="${homeDir}/.claude.json"
    SERVERS='${mcpServersToInject}'

    if [ ! -f "$CLAUDE_CONFIG" ]; then
      echo '{"mcpServers":{}}' > "$CLAUDE_CONFIG"
    fi

    ${pkgs.jq}/bin/jq --argjson servers "$SERVERS" '.mcpServers = (.mcpServers // {}) + $servers' "$CLAUDE_CONFIG" | ${pkgs.moreutils}/bin/sponge "$CLAUDE_CONFIG"
  '';

  nixSystemPaths = lib.concatStringsSep ":" [
    "${nodejs}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${username}/bin"
    "${homeDir}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

  crossPlatformMcpBridgeServiceSpecs = {
    chrome-devtools-mcp-bridge = {
      description = "Chrome DevTools MCP streamable HTTP bridge (supergateway)";
      launcher = chromeDevtoolsMcpStreamableHttpBridgeLauncher;
      linuxOnlyServiceExtraConfig = {
        MemoryMax = "2G";
      };
    };
    a2a-mcp-bridge = {
      description = "A2A MCP streamable HTTP bridge (supergateway)";
      launcher = a2aMcpStreamableHttpBridgeLauncher;
      linuxOnlyServiceExtraConfig = { };
    };
  };

  linuxOnlyMcpBridgeServiceSpecs = {
    browser-use-mcp-bridge = {
      description = "Browser-use MCP streamable HTTP bridge (supergateway)";
      launcher = browserUseMcpStreamableHttpBridgeLauncher;
      linuxOnlyServiceExtraConfig = { };
    };
  };
in
{
  imports = [
    (import ./mcps/mcp-bridge-runners.nix {
      inherit
        homeDir
        nixSystemPaths
        crossPlatformMcpBridgeServiceSpecs
        linuxOnlyMcpBridgeServiceSpecs
        ;
    })
    (import ./mcps/browser-use-config-patcher.nix {
      inherit browserUseConfigDir chromeBinary;
    })
  ];

  home = {
    packages = browserMcp.packages ++ twitterCli.packages;

    activation = {
      injectMcpServers = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${injectMcpServersIntoClaudeConfig}
      '';

      installChromeDevtoolsMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${browserMcp.installChromeDevtoolsMcpViaNpm}
      '';

      installSupergateway = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${browserMcp.installSupergatewayViaNpm}
      '';

      installA2aMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${a2aMcp.installA2aMcpViaNpm}
      '';
    };
  };
}
