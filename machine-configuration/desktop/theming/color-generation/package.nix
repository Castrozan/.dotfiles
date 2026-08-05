{ pkgs, binName }:
let
  colorGenerationSourcesDirectory = ./.;
  pythonWithColorLibraries = pkgs.python312.withPackages (
    pythonPackages: with pythonPackages; [
      colorthief
      pillow
    ]
  );
in
pkgs.writeShellScriptBin binName ''
  export PYTHONPATH="${colorGenerationSourcesDirectory}:''${PYTHONPATH:-}"
  exec ${pythonWithColorLibraries}/bin/python3 ${colorGenerationSourcesDirectory}/theme_generate_from_wallpaper.py "$@"
''
