{ pkgs, hostname }:
{
  name,
  source,
  runtimeInputs ? [ ],
}:
let
  testingPythonLibraryPath = ./scripts/lib;
  pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile source);
in
pkgs.writeShellScriptBin name (
  pkgs.lib.optionalString (runtimeInputs != [ ]) ''
    export PATH="${pkgs.lib.makeBinPath runtimeInputs}:$PATH"
  ''
  + ''
    export PYTHONPATH="${testingPythonLibraryPath}:''${PYTHONPATH:-}"
    export DOTFILES_BENCHMARK_HOST="${hostname}"
    exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
  ''
)
