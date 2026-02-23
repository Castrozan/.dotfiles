{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };

  mongodbCompassPackage = nixglWrap.wrapWithNixGLIntel {
    package = pkgs.mongodb-compass;
    binaries = [ "mongodb-compass" ];
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
