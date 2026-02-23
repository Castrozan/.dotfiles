{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  mongodbCompassPackage =
    if isNixOS then
      pkgs.mongodb-compass
    else
      let
        nixGLWrapper = inputs.nixgl.packages.${pkgs.stdenv.hostPlatform.system}.nixGLIntel;
        mongodbCompassWithNixGL = pkgs.writeShellScriptBin "mongodb-compass" ''
          exec ${nixGLWrapper}/bin/nixGLIntel ${pkgs.mongodb-compass}/bin/mongodb-compass "$@"
        '';
      in
      pkgs.symlinkJoin {
        name = "mongodb-compass-wrapped";
        paths = [
          mongodbCompassWithNixGL
          pkgs.mongodb-compass
        ];
      };
in
{
  home.packages = [ mongodbCompassPackage ];

  xdg.desktopEntries.mongodb-compass = {
    name = "MongoDB Compass";
    genericName = "MongoDB GUI";
    exec = "mongodb-compass %U";
    icon = "mongodb-compass";
    terminal = false;
    type = "Application";
    categories = [
      "Development"
      "Database"
    ];
    mimeType = [
      "x-scheme-handler/mongodb"
      "x-scheme-handler/mongodb+srv"
    ];
  };
}
