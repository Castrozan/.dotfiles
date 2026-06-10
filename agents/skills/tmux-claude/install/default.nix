{ pkgs }:
let
  scriptsDirectory = ../scripts;
in
{
  packages = [
    (pkgs.writeShellScriptBin "spawn-claude" ''
      export PATH="${pkgs.coreutils}/bin:${pkgs.findutils}/bin:${pkgs.gnugrep}/bin:${pkgs.tmux}/bin:$PATH"
      source ${scriptsDirectory}/tmux-helpers.sh
      ${builtins.readFile "${scriptsDirectory}/spawn-claude.sh"}
    '')
  ];
}
