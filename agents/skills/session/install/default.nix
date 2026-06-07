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
    (pkgs.writeShellScriptBin "claude-restart" ''
      export PATH="${pkgs.procps}/bin:${pkgs.tmux}/bin:${pkgs.findutils}/bin:${findClaudeAncestorProcessIdScript}/bin:$PATH"
      ${builtins.readFile "${scriptsDirectory}/claude-restart"}
    '')
    (pkgs.writeShellScriptBin "claude-show-session" ''
      export PATH="${pkgs.coreutils}/bin:${pkgs.gnused}/bin:${pkgs.jq}/bin:$PATH"
      ${builtins.readFile "${scriptsDirectory}/claude-show-session"}
    '')
  ];
}
