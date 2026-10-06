{ pkgs }:
let
  rilCliSource = ../scripts/ril_cli;

  rilCli = pkgs.writeShellScriptBin "ril" ''
    export PATH="${pkgs.git}/bin:${pkgs.openssh}/bin:${pkgs.gh}/bin:${pkgs.glab}/bin:''${PATH:+:$PATH}"
    export PYTHONPATH="${../../../development/forge/scripts}''${PYTHONPATH:+:$PYTHONPATH}"
    exec ${pkgs.python312}/bin/python ${rilCliSource}/ril.py "$@"
  '';
in
{
  packages = [ rilCli ];
}
