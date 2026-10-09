{ pkgs }:
pkgs.writeShellScriptBin "a2a" ''
  export PYTHONPATH=${./scripts}
  exec ${pkgs.python312}/bin/python3 -m a2a_cli "$@"
''
