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

  browserUseMcpOrphanReaper = pkgs.writeShellScript "browser-use-mcp-orphan-reaper" ''
    set -euo pipefail
    ${pkgs.procps}/bin/pkill -9 -f 'browser-use --mcp' || true
  '';

  browserUseMcpServerToInject = builtins.toJSON {
    browser-use = {
      type = "http";
      url = "http://localhost:${toString browserUseMcpStreamableHttpPort}/mcp";
    };
  };

  injectBrowserUseMcpIntoClaudeConfig = pkgs.writeShellScript "inject-browser-use-mcp" ''
    set -euo pipefail
    CLAUDE_CONFIG="${homeDir}/.claude.json"
    SERVERS='${browserUseMcpServerToInject}'

    if [ ! -f "$CLAUDE_CONFIG" ]; then
      echo '{"mcpServers":{}}' > "$CLAUDE_CONFIG"
    fi

    ${pkgs.jq}/bin/jq --argjson servers "$SERVERS" '.mcpServers = (.mcpServers // {}) + $servers' "$CLAUDE_CONFIG" | ${pkgs.moreutils}/bin/sponge "$CLAUDE_CONFIG"
  '';

  defaultBrowserUseProfileId = "nix-default";
  defaultBrowserUseConfig = builtins.toJSON {
    browser_profile = {
      "${defaultBrowserUseProfileId}" = {
        id = defaultBrowserUseProfileId;
        default = true;
        headless = false;
        executable_path = chromeBinary;
      };
    };
  };
  defaultBrowserUseConfigFile = pkgs.writeText "browseruse-default-config.json" defaultBrowserUseConfig;

  patchBrowserUseConfigWithChromeBinary = pkgs.writeShellScript "patch-browseruse-config-with-chrome-binary" ''
    set -euo pipefail
    CONFIG="${browserUseConfigDir}/config.json"
    mkdir -p "${browserUseConfigDir}"
    if [ ! -f "$CONFIG" ] || [ "$(${pkgs.jq}/bin/jq '.browser_profile | length' "$CONFIG" 2>/dev/null)" = "0" ] || [ "$(${pkgs.jq}/bin/jq '.browser_profile | length' "$CONFIG" 2>/dev/null)" = "null" ]; then
      cp --no-preserve=mode ${defaultBrowserUseConfigFile} "$CONFIG"
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
  home.activation = {
    writeBrowserUseConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${patchBrowserUseConfigWithChromeBinary}
    '';

    injectBrowserUseMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${injectBrowserUseMcpIntoClaudeConfig}
    '';
  };

  systemd.user.services.browser-use-mcp-bridge = {
    Unit = {
      Description = "Browser-use MCP streamable HTTP bridge (supergateway)";
      After = [ "graphical-session.target" ];
    };

    Service = {
      Type = "simple";
      ExecStartPre = "${browserUseMcpOrphanReaper}";
      ExecStart = "${browserUseMcpStreamableHttpBridgeWrapper}/bin/browser-use-mcp-streamable-http-bridge";
      Restart = "always";
      RestartSec = "3s";
      MemoryMax = "2G";
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
