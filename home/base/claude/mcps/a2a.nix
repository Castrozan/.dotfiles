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

  browserMcp = import ../../../../agents/skills/browser/install {
    inherit
      pkgs
      nodejs
      homeDir
      ;
    chromePackage = latest.google-chrome;
  };

  a2aMcp = import ../a2a-mcp-server/install {
    inherit
      pkgs
      nodejs
      homeDir
      ;
  };

  a2aMcpStreamableHttpPort = 8769;
  a2aMcpStreamableHttpSessionTimeoutMilliseconds = 60000;

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
      --stateful \
      --sessionTimeout ${toString a2aMcpStreamableHttpSessionTimeoutMilliseconds} \
      --port ${toString a2aMcpStreamableHttpPort}
  '';

  a2aMcpOrphanReaper = pkgs.writeShellScript "a2a-mcp-orphan-reaper" ''
    set -euo pipefail
    ${pkgs.procps}/bin/pkill -9 -f 'a2a-mcp-server-npm/bin/a2a-mcp-server' || true
  '';

  a2aMcpServerToInject = builtins.toJSON {
    a2a = {
      type = "http";
      url = "http://localhost:${toString a2aMcpStreamableHttpPort}/mcp";
    };
  };

  injectA2aMcpIntoClaudeConfig = pkgs.writeShellScript "inject-a2a-mcp" ''
    set -euo pipefail
    CLAUDE_CONFIG="${homeDir}/.claude.json"
    SERVERS='${a2aMcpServerToInject}'

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
  home.activation = {
    installA2aMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${a2aMcp.installA2aMcpViaNpm}
    '';

    injectA2aMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${injectA2aMcpIntoClaudeConfig}
    '';
  };

  systemd.user.services.a2a-mcp-bridge = {
    Unit = {
      Description = "A2A MCP streamable HTTP bridge (supergateway)";
      After = [ "graphical-session.target" ];
    };

    Service = {
      Type = "simple";
      ExecStartPre = "${a2aMcpOrphanReaper}";
      ExecStart = "${a2aMcpStreamableHttpBridgeWrapper}/bin/a2a-mcp-streamable-http-bridge";
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
