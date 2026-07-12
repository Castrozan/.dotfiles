{ pkgs }:
let
  colorGenerationSourcesDirectory = ./.;
  pythonWithColorLibraries = pkgs.python312.withPackages (
    pythonPackages: with pythonPackages; [
      colorthief
      pillow
    ]
  );
in
pkgs.writeShellApplication {
  name = "theme-regenerate-wallpaper-derived-colors";
  runtimeInputs = [ pkgs.git ];
  text = ''
    export PYTHONPATH="${colorGenerationSourcesDirectory}:''${PYTHONPATH:-}"
    exec ${pythonWithColorLibraries}/bin/python3 ${colorGenerationSourcesDirectory}/regenerate_wallpaper_derived_colors.py "$@"
  '';
}
