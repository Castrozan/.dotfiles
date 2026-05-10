{ pkgs }:
let
  scriptsDirectory = ../scripts;
in
{
  packages = [
    (pkgs.writeShellScriptBin "claude-exit" ''
      export PATH="${pkgs.procps}/bin:$PATH"
      ${builtins.readFile "${scriptsDirectory}/claude-exit"}
    '')
    (pkgs.writeShellScriptBin "claude-restart" ''
      export PATH="${pkgs.procps}/bin:${pkgs.tmux}/bin:${pkgs.findutils}/bin:$PATH"
      ${builtins.readFile "${scriptsDirectory}/claude-restart"}
    '')
    (pkgs.writeShellScriptBin "claude-show-session" ''
      export PATH="${pkgs.coreutils}/bin:${pkgs.gnused}/bin:${pkgs.jq}/bin:$PATH"
      ${builtins.readFile "${scriptsDirectory}/claude-show-session"}
    '')
  ];
}
