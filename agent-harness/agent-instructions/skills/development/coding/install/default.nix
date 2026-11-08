{ pkgs }:
let
  python = pkgs.python312;

  codingScriptsSource = ../scripts;

  gitHistory = pkgs.writeShellScriptBin "git-history" ''
    set -euo pipefail
    export PATH="${pkgs.git}/bin:${pkgs.coreutils}/bin:${pkgs.gnugrep}/bin:''${PATH:+:$PATH}"
    exec ${python}/bin/python3 ${codingScriptsSource}/git-history.py "$@"
  '';

  swarmBatchGate = pkgs.writeShellScriptBin "swarm-batch-gate" ''
    exec ${python}/bin/python3 ${codingScriptsSource}/swarm-batch-gate.py "$@"
  '';

  swarmDifferentialCheck = pkgs.writeShellScriptBin "swarm-differential-check" ''
    export PATH="${pkgs.git}/bin''${PATH:+:$PATH}"
    exec ${python}/bin/python3 ${codingScriptsSource}/swarm-differential-check.py "$@"
  '';
in
{
  packages = [
    gitHistory
    swarmBatchGate
    swarmDifferentialCheck
  ];
}
