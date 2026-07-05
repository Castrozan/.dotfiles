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
  homepageConfigFiles = {
    "settings.yaml" = ./homepage/settings.yaml;
    "services.yaml" = ./homepage/services.yaml;
    "widgets.yaml" = ./homepage/widgets.yaml;
    "bookmarks.yaml" = ./homepage/bookmarks.yaml;
  };
  deployHomepageConfigCommand = lib.concatStringsSep "\n" (
    lib.mapAttrsToList (fileName: source: ''
      $DRY_RUN_CMD rm -f "${stackRoot}/config/homepage/${fileName}"
      $DRY_RUN_CMD install -D -m 0644 ${source} "${stackRoot}/config/homepage/${fileName}"
    '') homepageConfigFiles
  );
in
lib.mkIf isChise {
  home = {
    file = {
      "arr-stack/docker-compose.yml".source = ./docker-compose.yml;
      "arr-stack/.env".source = ./env;
      "arr-stack/README.md".source = ./README.md;
    };

    activation.createArrStackPersistenceDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      ${makePersistenceDirectoriesCommand}
    '';

    activation.deployArrStackHomepageConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      ${deployHomepageConfigCommand}
    '';
  };
}
