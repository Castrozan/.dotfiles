{ pkgs }:
pkgs.writeShellScriptBin "a2a" ''
  export PYTHONPATH=${./scripts}:${../../servants}:${../../hooks/runtime/common}
  exec ${pkgs.python312}/bin/python3 -m a2a_cli "$@"
''
