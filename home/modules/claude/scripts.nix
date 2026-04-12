{ pkgs, ... }:
let
  projectAgentInstructionsFile = ./project-agent/instructions.md;
  launchProjectAgentScript = pkgs.writeShellScriptBin "launch-project-agent" ''
    export PROJECT_AGENT_INSTRUCTIONS="${projectAgentInstructionsFile}"
    exec ${pkgs.python312}/bin/python3 ${./scripts/launch-project-agent} "$@"
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
    launchProjectAgentScript
  ];
}
