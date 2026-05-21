{ pkgs, config, ... }:
let
  projectAgentInstructionsFile = ./persistent-agents/instructions.md;
  claudeAgentScript = pkgs.writeShellScriptBin "claude-agent" ''
    export PROJECT_AGENT_INSTRUCTIONS="${projectAgentInstructionsFile}"
    export CLAUDE_BINARY_PATH="${config.claude.package}/bin/claude"
    exec ${pkgs.python312}/bin/python3 ${./scripts/claude-agent} "$@"
  '';
  procUtilsBinPath = "${pkgs.procps}/bin";
  claudeExitScript = pkgs.writeShellScriptBin "claude-exit" ''
    export PATH="${procUtilsBinPath}:$PATH"
    ${builtins.readFile ./scripts/claude-exit}
  '';
  claudeRestartScript = pkgs.writeShellScriptBin "claude-restart" ''
    export PATH="${procUtilsBinPath}:${pkgs.tmux}/bin:$PATH"
    ${builtins.readFile ./scripts/claude-restart}
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
in
{
  home.packages = [
    claudeAgentScript
    claudeExitScript
    claudeRestartScript
    claudeUpdateVersionScript
    memoryWriteScript
    memoryPruneScript
  ];
}
