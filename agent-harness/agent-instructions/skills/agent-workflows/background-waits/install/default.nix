{ pkgs }:
let
  waitGuardModules = ../../../../../hooks/runtime/pre-tool-use/common;
in
{
  packages = [
    (pkgs.writeShellScriptBin "background-wait-tracker" ''
      export PYTHONPATH="${../scripts}:${waitGuardModules}''${PYTHONPATH:+:$PYTHONPATH}"
      exec ${pkgs.python312}/bin/python3 -m background_wait_tracker "$@"
    '')
    (pkgs.writeShellScriptBin "wait-for-event" ''
      export PATH="${pkgs.coreutils}/bin''${PATH:+:$PATH}"
      export PYTHONPATH="${../scripts}''${PYTHONPATH:+:$PYTHONPATH}"
      exec ${pkgs.python312}/bin/python3 -m wait_for_event "$@"
    '')
  ];
}
