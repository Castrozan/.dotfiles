{
  homeDir,
  chromeDevtoolsMcpStdioCommand,
  chromeDevtoolsMcpStdioArgs,
  braveDevtoolsMcpStdioCommand,
  braveDevtoolsMcpStdioArgs,
  a2aMcpStdioCommand,
  a2aMcpStdioArgs,
  browserUseMcpStdioCommand,
  codexBinaryPath,
}:
{ pkgs, lib, ... }:
let
  desiredMcpServersToInject = {
    chrome-devtools = {
      command = chromeDevtoolsMcpStdioCommand;
      args = chromeDevtoolsMcpStdioArgs;
    };
    brave-devtools = {
      command = braveDevtoolsMcpStdioCommand;
      args = braveDevtoolsMcpStdioArgs;
    };
    codex = {
      command = codexBinaryPath;
      args = [ "mcp-server" ];
    };
    a2a = {
      command = a2aMcpStdioCommand;
      args = a2aMcpStdioArgs;
    };
    browser-use = {
      command = browserUseMcpStdioCommand;
      args = [ ];
    };
  };

  mcpServerNamesManagedAcrossAllPlatforms = [
    "a2a"
    "brave-devtools"
    "browser-use"
    "chrome-devtools"
    "codex"
  ];

  desiredMcpServersJson = builtins.toJSON desiredMcpServersToInject;
  managedMcpServerNamesJson = builtins.toJSON mcpServerNamesManagedAcrossAllPlatforms;

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
