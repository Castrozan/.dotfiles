{ pkgs, ... }:
let
  launchProjectAgentScript = pkgs.writers.writePython3Bin "launch-project-agent" {
    flakeIgnore = [
      "E265"
      "E501"
      "W503"
    ];
  } (builtins.readFile ./scripts/launch-project-agent);
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
