{ pkgs }:
pkgs.writeShellScriptBin "orchestrator" ''
  export PYTHONPATH=${./scripts}
  exec ${pkgs.python312}/bin/python3 -m orchestrator_cli "$@"
''
