{ pkgs, ... }:
let
  mkSystemPythonScript =
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
    (pkgs.writeShellScriptBin "rebuild" (builtins.readFile ./scripts/rebuild))
    (mkSystemPythonScript "nix-gc" ./scripts/nix_gc.py)
    (pkgs.writeShellScriptBin "tar-unzip2dir" (builtins.readFile ./scripts/tar-unzip2dir))
    (mkSystemPythonScript "mouse-poll-rate" ./scripts/mouse_poll_rate.py)
  ];
}
