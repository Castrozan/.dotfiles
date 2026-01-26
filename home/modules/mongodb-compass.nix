{ pkgs, ... }:
let
  mongodbCompassFlags = "--ozone-platform=x11 --disable-gpu";
in
{
  home.packages = [ pkgs.mongodb-compass ];

  xdg.desktopEntries.mongodb-compass = {
    name = "MongoDB Compass";
    genericName = "MongoDB GUI";
    comment = "The official GUI for MongoDB";
    exec = "mongodb-compass ${mongodbCompassFlags} %U";
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
