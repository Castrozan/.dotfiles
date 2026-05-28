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

  chromeDevtoolsMcpServerToInject = builtins.toJSON {
    chrome-devtools = {
      type = "http";
      url = browserMcp.mcpServerStreamableHttpUrl;
    };
  };

  injectChromeDevtoolsMcpIntoClaudeConfig = pkgs.writeShellScript "inject-chrome-devtools-mcp" ''
    set -euo pipefail
    CLAUDE_CONFIG="${homeDir}/.claude.json"
    SERVERS='${chromeDevtoolsMcpServerToInject}'

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
    packages = browserMcp.packages;

    activation = {
      installChromeDevtoolsMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${browserMcp.installChromeDevtoolsMcpViaNpm}
      '';

      installSupergateway = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${browserMcp.installSupergatewayViaNpm}
      '';

      injectChromeDevtoolsMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${injectChromeDevtoolsMcpIntoClaudeConfig}
      '';
    };
  };

  systemd.user.services.chrome-devtools-mcp-bridge = {
    Unit = {
      Description = "Chrome DevTools MCP streamable HTTP bridge (supergateway)";
      After = [ "graphical-session.target" ];
    };

    Service = {
      Type = "simple";
      ExecStartPre = "${browserMcp.chromeDevtoolsMcpOrphanReaper}";
      ExecStart = browserMcp.streamableHttpBridgeCommand;
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
