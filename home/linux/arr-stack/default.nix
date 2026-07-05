{
  config,
  lib,
  hostname,
  ...
}:
let
  isChise = hostname == "chise";
  stackRoot = "${config.home.homeDirectory}/arr-stack";
  configServiceDirectories = [
    "qbittorrent"
    "prowlarr"
    "sonarr"
    "radarr"
    "lidarr"
    "readarr"
    "bazarr"
    "jellyfin"
    "jellyseerr"
    "homepage"
  ];
  dataDirectories = [
    "torrents"
    "media/tv"
    "media/movies"
    "media/music"
    "media/books"
  ];
  configDirectoriesToCreate = map (
    service: "${stackRoot}/config/${service}"
  ) configServiceDirectories;
  dataDirectoriesToCreate = map (directory: "${stackRoot}/data/${directory}") dataDirectories;
  allPersistenceDirectories = configDirectoriesToCreate ++ dataDirectoriesToCreate;
  makePersistenceDirectoriesCommand = lib.concatMapStringsSep "\n" (
    directory: ''$DRY_RUN_CMD mkdir -p $VERBOSE_ARG "${directory}"''
  ) allPersistenceDirectories;
in
lib.mkIf isChise {
  home.file = {
    "arr-stack/docker-compose.yml".source = ./docker-compose.yml;
    "arr-stack/.env".source = ./env;
    "arr-stack/README.md".source = ./README.md;
    "arr-stack/config/homepage/settings.yaml".source = ./homepage/settings.yaml;
    "arr-stack/config/homepage/services.yaml".source = ./homepage/services.yaml;
    "arr-stack/config/homepage/widgets.yaml".source = ./homepage/widgets.yaml;
    "arr-stack/config/homepage/bookmarks.yaml".source = ./homepage/bookmarks.yaml;
  };

  home.activation.createArrStackPersistenceDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    ${makePersistenceDirectoriesCommand}
  '';
}
