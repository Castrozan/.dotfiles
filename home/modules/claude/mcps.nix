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
  chromeBinary = "${latest.google-chrome}/bin/google-chrome-stable";

  scraplingFetchMcpWrapper = pkgs.writeShellScript "scrapling-mcp" ''
    export PLAYWRIGHT_BROWSERS_PATH="$HOME/.local/share/scrapling-browsers"
    exec "$HOME/.local/share/scrapling-venv/bin/python" -m scrapling_fetch_mcp.mcp "$@"
  '';

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

  a2aMcp = import ../../../agents/skills/openclaw/a2a-mcp-default.nix {
    inherit
      pkgs
      nodejs
      homeDir
      ;
  };

  twitterCli = import ../../../agents/skills/comms/twitter-cli.nix {
    inherit
      pkgs
      homeDir
      ;
  };

  mcpServersToInject = builtins.toJSON {
    chrome-devtools = {
      command = browserMcp.mcpServerCommand;
      args = [ ];
    };
    browser-use = {
      command = "${browserUseMcpWrapper}";
      args = [ ];
    };
    scrapling-fetch = {
      command = "${scraplingFetchMcpWrapper}";
      args = [ ];
    };
    codex = {
      command = "${homeDir}/.local/bin/codex";
      args = [ "mcp-server" ];
    };
    a2a = {
      command = a2aMcp.mcpServerCommand;
      args = a2aMcp.mcpServerArgs;
    };
  };

  injectMcpServersIntoClaudeConfig = pkgs.writeShellScript "inject-mcp-servers" ''
    set -euo pipefail
    CLAUDE_CONFIG="${homeDir}/.claude.json"
    SERVERS='${mcpServersToInject}'

    if [ ! -f "$CLAUDE_CONFIG" ]; then
      echo '{"mcpServers":{}}' > "$CLAUDE_CONFIG"
    fi

    ${pkgs.jq}/bin/jq --argjson servers "$SERVERS" '.mcpServers = (.mcpServers // {}) * $servers' "$CLAUDE_CONFIG" | ${pkgs.moreutils}/bin/sponge "$CLAUDE_CONFIG"
  '';
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

      writeBrowserUseConfig =
        let
          patchScript = pkgs.writeShellScript "patch-browseruse-config" ''
            set -euo pipefail
            CONFIG="${browserUseConfigDir}/config.json"
            mkdir -p "${browserUseConfigDir}"
            if [ ! -f "$CONFIG" ]; then
              echo '{}' > "$CONFIG"
            fi
            ${pkgs.jq}/bin/jq '
              .browser_profile = (
                .browser_profile // {} |
                to_entries |
                map(.value.executable_path = "${chromeBinary}" | .value.headless = false) |
                from_entries
              )
            ' "$CONFIG" | ${pkgs.moreutils}/bin/sponge "$CONFIG"
          '';
        in
        lib.hm.dag.entryAfter [ "writeBoundary" ] ''
          run ${patchScript}
        '';

      installA2aMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${a2aMcp.installA2aMcpViaNpm}
      '';
    };
  };
}
