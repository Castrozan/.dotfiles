{ pkgs }:
let
  python = pkgs.python312;

  gitHistorySource = pkgs.writeText "git-history.py" (builtins.readFile ../scripts/git-history.py);

  gitHistory = pkgs.writeShellScriptBin "git-history" ''
    set -euo pipefail
    export PATH="${pkgs.git}/bin:${pkgs.coreutils}/bin:${pkgs.gnugrep}/bin:''${PATH:+:$PATH}"
    exec ${python}/bin/python3 ${gitHistorySource} "$@"
  '';
in
{
  packages = [ gitHistory ];
}
