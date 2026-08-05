{ pkgs }:
name: file:
let
  pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile file);
in
pkgs.writeShellScriptBin name ''
  exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
''
