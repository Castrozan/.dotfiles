{ pkgs, config, ... }:
let
  projectAgentInstructionsFile = ./persistent-agents/instructions.md;
  claudeAgentScript = pkgs.writeShellScriptBin "claude-agent" ''
    export PROJECT_AGENT_INSTRUCTIONS="${projectAgentInstructionsFile}"
    export CLAUDE_BINARY_PATH="${config.claude.package}/bin/claude"
    exec ${pkgs.python312}/bin/python3 ${./scripts/claude-agent} "$@"
  '';
  claudeUpdateVersionScript = pkgs.writeShellScriptBin "claude-update-version" ''
    export PATH="${pkgs.nix}/bin:${pkgs.git}/bin:$PATH"
    exec ${pkgs.python312}/bin/python3 ${./scripts/claude-update-version} "$@"
  '';
  memoryWriteScript = pkgs.writeShellScriptBin "memory-write" ''
    exec ${pkgs.python312}/bin/python3 ${./scripts/memory-write} "$@"
  '';
  memoryPruneScript = pkgs.writeShellScriptBin "memory-prune" ''
    exec ${pkgs.python312}/bin/python3 ${./scripts/memory-prune} "$@"
  '';
  claudeA2aPeerScript = pkgs.writeShellScriptBin "claude-a2a-peer" ''
    export PATH="${pkgs.tmux}/bin:$PATH"
    export PYTHONPATH=${../../../agents}
    exec ${pkgs.python312}/bin/python3 ${./scripts/claude-a2a-peer} "$@"
  '';
in
{
  home.packages = [
    claudeAgentScript
    claudeUpdateVersionScript
    memoryWriteScript
    memoryPruneScript
    claudeA2aPeerScript
  ];
}
