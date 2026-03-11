{ pkgs, ... }:
let
  mkTestingPythonScript =
    name: file:
    let
      pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile file);
    in
    pkgs.writeShellScriptBin name ''
      exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
    '';
in
{
  home.packages = [
    (mkTestingPythonScript "benchmark-rebuild" ./scripts/benchmark_rebuild.py)
    (mkTestingPythonScript "benchmark-shell" ./scripts/benchmark_shell.py)
  ];
}
