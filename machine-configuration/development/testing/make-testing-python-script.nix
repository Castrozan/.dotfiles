{ pkgs }:
name: file:
let
  testingPythonLibraryPath = ./scripts/lib;
  pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile file);
in
pkgs.writeShellScriptBin name ''
  export PYTHONPATH="${testingPythonLibraryPath}:''${PYTHONPATH:-}"
  exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
''
