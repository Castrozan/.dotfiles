{ pkgs, hostname, ... }:
let
  rebuild = import ../development/system-rebuild/scripts/rebuild { inherit pkgs hostname; };
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
  imports = [ ../desktop/input/mouse/mouse-polling-rate-home-manager.nix ];

  home.packages = [
    rebuild
    (mkSystemPythonScript "nix-gc" ./nix-store-maintenance/scripts/nix_gc.py)
    (pkgs.writeShellScriptBin "tar-unzip2dir" (
      builtins.readFile ./archive-extraction/scripts/tar-unzip2dir
    ))
  ];
}
