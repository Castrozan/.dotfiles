{ pkgs, config, ... }:
let
  projectAgentInstructionsFile = ./persistent-agents/instructions.md;
  claudeAgentScript = pkgs.writeShellScriptBin "claude-agent" ''
    export PROJECT_AGENT_INSTRUCTIONS="${projectAgentInstructionsFile}"
    export CLAUDE_BINARY_PATH="${config.claude.package}/bin/claude"
    exec ${pkgs.python312}/bin/python3 ${./scripts/claude-agent} "$@"
  '';
in
{
  home.packages = [ claudeAgentScript ];
}
