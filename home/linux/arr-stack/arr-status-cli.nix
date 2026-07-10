{ pkgs, stackRoot }:
let
  arrStatusPackageDirectory = ./scripts/arr_status;
in
pkgs.writeShellScriptBin "arr-status" ''
  set -Eeuo pipefail

  export ARR_STATUS_STACK_HOME="''${ARR_STATUS_STACK_HOME:-${stackRoot}}"

  exec ${pkgs.python312}/bin/python3 ${arrStatusPackageDirectory}/__main__.py "$@"
''
