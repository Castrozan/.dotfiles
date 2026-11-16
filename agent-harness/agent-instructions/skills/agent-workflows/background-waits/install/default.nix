{ pkgs }:
let
  waitGuardModules = ../../../../../hooks/runtime/pre-tool-use/common;
in
{
  packages = [
    (pkgs.writeShellScriptBin "background-wait-tracker" ''
      export PATH="${pkgs.ripgrep}/bin''${PATH:+:$PATH}"
      export PYTHONPATH="${../scripts}:${waitGuardModules}''${PYTHONPATH:+:$PYTHONPATH}"
      exec ${pkgs.python312}/bin/python3 -m background_wait_tracker "$@"
    '')
  ];
}
