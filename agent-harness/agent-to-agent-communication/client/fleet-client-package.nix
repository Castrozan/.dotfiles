{ pkgs }:
pkgs.writeShellScriptBin "dot-fleet" ''
  export PYTHONPATH=${./scripts}
  exec ${pkgs.python312}/bin/python3 -m a2a_cli.fleet "$@"
''
