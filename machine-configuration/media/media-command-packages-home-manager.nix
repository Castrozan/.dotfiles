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
    (pkgs.writeShellScriptBin "on" (builtins.readFile ./obsidian/scripts/open-new-note))
    (pkgs.writeShellScriptBin "pdf-edit" (
      builtins.readFile ./pdf-editing/scripts/start-bentopdf-pdf-editor
    ))
    (mkMediaPythonScript "speed-read" ./speed-reading/scripts/speed_read.py)
  ];
}
