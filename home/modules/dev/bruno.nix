{ pkgs, lib, ... }:
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
      defaultCollectionPath = "/home/zanoni/vault/bruno-collections";
      theme = "dark";
    };
  };

  home.activation.createBrunoCollections = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run mkdir -p /home/zanoni/vault/bruno-collections
  '';
}
