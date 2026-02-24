{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglSystem = pkgs.stdenv.hostPlatform.system;
  nixGLIntelPackage = inputs.nixgl.packages.${nixglSystem}.nixGLIntel;

  mongodbCompassWrappedBinary = pkgs.writeShellScriptBin "mongodb-compass" (
    if isNixOS then
      ''
        exec ${pkgs.mongodb-compass}/bin/mongodb-compass --ignore-additional-command-line-flags --password-store=gnome-libsecret "$@"
      ''
    else
      ''
        exec ${nixGLIntelPackage}/bin/nixGLIntel ${pkgs.mongodb-compass}/bin/mongodb-compass --ignore-additional-command-line-flags --password-store=gnome-libsecret "$@"
      ''
  );

  mongodbCompassPackage = pkgs.symlinkJoin {
    name = "mongodb-compass-wrapped";
    paths = [
      mongodbCompassWrappedBinary
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
