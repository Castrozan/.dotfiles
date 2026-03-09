{
  pkgs,
  lib,
  config,
  ...
}:
let
  brunoCollectionDirectory = "${config.home.homeDirectory}/vault/bruno-collections";
in
{
  home.packages = [ pkgs.bruno ];

  xdg.desktopEntries.bruno = {
    name = "Bruno";
    genericName = "API Client";
    comment = "Opensource IDE for exploring and testing APIs";
    exec = "bruno %U";
    icon = "bruno";
    terminal = false;
    type = "Application";
    categories = [
      "Development"
      "Network"
      "WebDevelopment"
    ];
  };

  xdg.configFile."bruno/preferences.json".text = builtins.toJSON {
    version = "1";
    preferences = {
      defaultCollectionPath = brunoCollectionDirectory;
      theme = "dark";
    };
  };

  home.activation.createBrunoCollections = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run mkdir -p "${brunoCollectionDirectory}"
  '';
}
