{ pkgs, config, ... }:
let
  projectAgentInstructionsFile = ./project-agent/instructions.md;
  claudeAgentScript = pkgs.writeShellScriptBin "claude-agent" ''
    export PROJECT_AGENT_INSTRUCTIONS="${projectAgentInstructionsFile}"
    export CLAUDE_BINARY_PATH="${config.claude.package}/bin/claude"
    exec ${pkgs.python312}/bin/python3 ${./scripts/claude-agent} "$@"
  '';
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "claude-exit" ''
      export PATH="${pkgs.procps}/bin:$PATH"
      ${builtins.readFile ./scripts/claude-exit}
    '')
    (pkgs.writeShellScriptBin "claude-restart" ''
      export PATH="${pkgs.procps}/bin:${pkgs.tmux}/bin:${pkgs.findutils}/bin:$PATH"
      ${builtins.readFile ./scripts/claude-restart}
    '')
    (pkgs.writeShellScriptBin "claude-show-session" ''
      export PATH="${pkgs.coreutils}/bin:${pkgs.gnused}/bin:${pkgs.jq}/bin:$PATH"
      ${builtins.readFile ./scripts/claude-show-session}
    '')
    claudeAgentScript
  ];
}
