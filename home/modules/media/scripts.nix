{ pkgs, ... }:
let
  mkMediaPythonScript =
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
    (mkMediaPythonScript "daily-note" ./scripts/daily_note.py)
    (pkgs.writeShellScriptBin "on" (builtins.readFile ./scripts/on))
    (pkgs.writeShellScriptBin "pdf-edit" (builtins.readFile ./scripts/pdf-edit))
    (mkMediaPythonScript "speed-read" ./scripts/speed_read.py)
  ];
}
