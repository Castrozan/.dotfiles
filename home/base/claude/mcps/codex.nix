{
  pkgs,
  config,
  lib,
  ...
}:
let
  homeDir = config.home.homeDirectory;

  codexMcpServerToInject = builtins.toJSON {
    codex = {
      command = "${homeDir}/.local/bin/codex";
      args = [ "mcp-server" ];
    };
  };

  injectCodexMcpIntoClaudeConfig = pkgs.writeShellScript "inject-codex-mcp" ''
    set -euo pipefail
    CLAUDE_CONFIG="${homeDir}/.claude.json"
    SERVERS='${codexMcpServerToInject}'

    if [ ! -f "$CLAUDE_CONFIG" ]; then
      echo '{"mcpServers":{}}' > "$CLAUDE_CONFIG"
    fi

    ${pkgs.jq}/bin/jq --argjson servers "$SERVERS" '.mcpServers = (.mcpServers // {}) + $servers' "$CLAUDE_CONFIG" | ${pkgs.moreutils}/bin/sponge "$CLAUDE_CONFIG"
  '';
in
{
  home.activation.injectCodexMcp = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${injectCodexMcpIntoClaudeConfig}
  '';
}
