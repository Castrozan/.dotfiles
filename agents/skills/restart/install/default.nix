{ pkgs }:
let
  scriptsDirectory = ../scripts;
  findClaudeAncestorProcessIdScript = pkgs.writeShellScriptBin "find-claude-ancestor-pid" ''
    export PATH="${pkgs.procps}/bin:$PATH"
    ${builtins.readFile ../../exit/scripts/find-claude-ancestor-pid}
  '';
in
{
  packages = [
    (pkgs.writeShellScriptBin "claude-restart" ''
      export PATH="${pkgs.procps}/bin:${pkgs.tmux}/bin:${pkgs.findutils}/bin:${findClaudeAncestorProcessIdScript}/bin:$PATH"
      ${builtins.readFile "${scriptsDirectory}/claude-restart"}
    '')
  ];
}
