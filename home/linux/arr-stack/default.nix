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
    "gluetun"
    "qbittorrent"
    "prowlarr"
    "sonarr"
    "radarr"
    "lidarr"
    "readarr"
    "bazarr"
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
  };

  home.activation.createArrStackPersistenceDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    ${makePersistenceDirectoriesCommand}
  '';
}
