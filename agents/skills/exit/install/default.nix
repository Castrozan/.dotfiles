{ pkgs }:
let
  scriptsDirectory = ../scripts;
  findClaudeAncestorProcessIdScript = pkgs.writeShellScriptBin "find-claude-ancestor-pid" ''
    export PATH="${pkgs.procps}/bin:$PATH"
    ${builtins.readFile "${scriptsDirectory}/find-claude-ancestor-pid"}
  '';
in
{
  packages = [
    findClaudeAncestorProcessIdScript
    (pkgs.writeShellScriptBin "claude-exit" ''
      export PATH="${pkgs.procps}/bin:${findClaudeAncestorProcessIdScript}/bin:$PATH"
      ${builtins.readFile "${scriptsDirectory}/claude-exit"}
    '')
  ];
}
