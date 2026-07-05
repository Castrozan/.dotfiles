{
  homeDir,
  mcpServerDefinitions,
}:
{ pkgs, lib, ... }:
let
  desiredMcpServersJson = builtins.toJSON mcpServerDefinitions;
  managedMcpServerNamesJson = builtins.toJSON (builtins.attrNames mcpServerDefinitions);

  injectMcpServersIntoClaudeConfig = pkgs.writeShellScript "inject-mcp-servers" ''
    set -euo pipefail
    CLAUDE_CONFIG="${homeDir}/.claude.json"
    DESIRED_SERVERS='${desiredMcpServersJson}'
    MANAGED_SERVER_NAMES='${managedMcpServerNamesJson}'

    if [ ! -f "$CLAUDE_CONFIG" ]; then
      echo '{"mcpServers":{}}' > "$CLAUDE_CONFIG"
    fi

    ${pkgs.jq}/bin/jq \
      --argjson desired "$DESIRED_SERVERS" \
      --argjson managed "$MANAGED_SERVER_NAMES" \
      '.mcpServers = (
        ((.mcpServers // {}) | with_entries(select(.key as $key | $managed | index($key) | not)))
        + $desired
      )' \
      "$CLAUDE_CONFIG" | ${pkgs.moreutils}/bin/sponge "$CLAUDE_CONFIG"
  '';
in
{
  home.activation.injectMcpServers = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${injectMcpServersIntoClaudeConfig}
  '';
}
