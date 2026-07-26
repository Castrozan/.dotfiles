{ pkgs }:
let
  rilCliSource = ../scripts/ril_cli;

  rilCli = pkgs.writeShellScriptBin "ril" ''
    exec ${pkgs.python312}/bin/python ${rilCliSource}/ril.py "$@"
  '';
in
{
  packages = [ rilCli ];
}
