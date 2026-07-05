{ pkgs }:
let
  python = pkgs.python312;

  gitHistorySource = ../scripts;

  gitHistory = pkgs.writeShellScriptBin "git-history" ''
    set -euo pipefail
    export PATH="${pkgs.git}/bin:${pkgs.coreutils}/bin:${pkgs.gnugrep}/bin:''${PATH:+:$PATH}"
    exec ${python}/bin/python3 ${gitHistorySource}/git-history.py "$@"
  '';
in
{
  packages = [ gitHistory ];
}
