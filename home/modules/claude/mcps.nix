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
  chromeBinary = "${latest.google-chrome}/bin/google-chrome-stable";

  browserMcp = import ../../../agents/skills/browser {
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

  browserUseMcpStreamableHttpBridgeWrapper = pkgs.writeShellScriptBin "browser-use-mcp-streamable-http-bridge" ''
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

  a2aMcp = import ../../../agents/skills/openclaw/a2a-mcp-default.nix {
    inherit
      pkgs
      nodejs
      homeDir
      ;
  };

  a2aMcpStreamableHttpPort = 8769;

  a2aMcpStreamableHttpBridgeWrapper = pkgs.writeShellScriptBin "a2a-mcp-streamable-http-bridge" ''
    set -euo pipefail
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"

    if ! "${browserMcp.supergatewayBinary}" --version >/dev/null 2>&1; then
      echo "supergateway binary not found at ${browserMcp.supergatewayBinary}" >&2
      exit 1
    fi

    exec "${browserMcp.supergatewayBinary}" \
      --stdio "${a2aMcp.mcpServerCommand} ${builtins.head a2aMcp.mcpServerArgs}" \
      --outputTransport streamableHttp \
      --port ${toString a2aMcpStreamableHttpPort}
  '';

  twitterCli = import ../../../agents/skills/comms/twitter-cli.nix {
    inherit
      pkgs
      homeDir
      ;
  };

  mcpServersToInject = builtins.toJSON {
    chrome-devtools = {
      type = "http";
      url = browserMcp.mcpServerStreamableHttpUrl;
    };
    browser-use = {
      type = "http";
      url = "http://localhost:${toString browserUseMcpStreamableHttpPort}/mcp";
    };
    codex = {
      command = "${homeDir}/.local/bin/codex";
      args = [ "mcp-server" ];
    };
    a2a = {
      type = "http";
      url = "http://localhost:${toString a2aMcpStreamableHttpPort}/mcp";
    };
  };

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
in
{
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

      writeBrowserUseConfig =
        let
          defaultProfileId = "nix-default";
          defaultConfig = builtins.toJSON {
            browser_profile = {
              "${defaultProfileId}" = {
                id = defaultProfileId;
                default = true;
                headless = false;
                executable_path = chromeBinary;
              };
            };
          };
          defaultConfigFile = pkgs.writeText "browseruse-default-config.json" defaultConfig;
          patchBrowserUseConfigWithChromeBinary = pkgs.writeShellScript "patch-browseruse-config-with-chrome-binary" ''
            set -euo pipefail
            CONFIG="${browserUseConfigDir}/config.json"
            mkdir -p "${browserUseConfigDir}"
            if [ ! -f "$CONFIG" ] || [ "$(${pkgs.jq}/bin/jq '.browser_profile | length' "$CONFIG" 2>/dev/null)" = "0" ] || [ "$(${pkgs.jq}/bin/jq '.browser_profile | length' "$CONFIG" 2>/dev/null)" = "null" ]; then
              cp --no-preserve=mode ${defaultConfigFile} "$CONFIG"
            else
              ${pkgs.jq}/bin/jq '
                .browser_profile |= (
                  to_entries |
                  map(.value.executable_path = "${chromeBinary}" | .value.headless = false) |
                  from_entries
                )
              ' "$CONFIG" | ${pkgs.moreutils}/bin/sponge "$CONFIG"
            fi
          '';
        in
        lib.hm.dag.entryAfter [ "writeBoundary" ] ''
          run ${patchBrowserUseConfigWithChromeBinary}
        '';

      installA2aMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${a2aMcp.installA2aMcpViaNpm}
      '';
    };
  };

  systemd.user.services.browser-use-mcp-bridge = {
    Unit = {
      Description = "Browser-use MCP streamable HTTP bridge (supergateway)";
      After = [ "graphical-session.target" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${browserUseMcpStreamableHttpBridgeWrapper}/bin/browser-use-mcp-streamable-http-bridge";
      Restart = "always";
      RestartSec = "3s";
      Environment = [
        "PATH=${nixSystemPaths}"
        "HOME=${homeDir}"
      ];
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };

  systemd.user.services.a2a-mcp-bridge = {
    Unit = {
      Description = "A2A MCP streamable HTTP bridge (supergateway)";
      After = [ "graphical-session.target" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${a2aMcpStreamableHttpBridgeWrapper}/bin/a2a-mcp-streamable-http-bridge";
      Restart = "always";
      RestartSec = "3s";
      Environment = [
        "PATH=${nixSystemPaths}"
        "HOME=${homeDir}"
      ];
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };

  systemd.user.services.chrome-devtools-mcp-bridge = {
    Unit = {
      Description = "Chrome DevTools MCP streamable HTTP bridge (supergateway)";
      After = [ "graphical-session.target" ];
    };

    Service = {
      Type = "simple";
      ExecStart = browserMcp.streamableHttpBridgeCommand;
      Restart = "always";
      RestartSec = "3s";
      Environment = [
        "PATH=${nixSystemPaths}"
        "HOME=${homeDir}"
      ];
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };
}
