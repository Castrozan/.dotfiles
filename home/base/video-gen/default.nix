{
  pkgs,
  lib,
  ...
}:
let
  videoGeneratorPackageRoot = lib.fileset.toSource {
    root = ./.;
    fileset = ./generate_video;
  };

  videoGenerationCommand = pkgs.writeShellScriptBin "video-gen" ''
    export PYTHONPATH="${videoGeneratorPackageRoot}''${PYTHONPATH:+:$PYTHONPATH}"
    exec ${pkgs.python312}/bin/python -m generate_video "$@"
  '';
in
{
  home.packages = [ videoGenerationCommand ];
}
