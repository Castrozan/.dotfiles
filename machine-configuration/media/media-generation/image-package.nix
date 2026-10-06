{ pkgs }:
let
  imagePython = pkgs.python312.withPackages (import ./image-python-packages.nix);
in
pkgs.writeShellScriptBin "media-image" ''
  export PYTHONDONTWRITEBYTECODE=1
  exec ${imagePython}/bin/python3 ${./scripts}/media_image_cli.py "$@"
''
