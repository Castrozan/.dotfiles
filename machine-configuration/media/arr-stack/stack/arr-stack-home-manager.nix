{
  config,
  lib,
  pkgs,
  hostname,
  ...
}:
let
  isChise = hostname == "chise";
  stackRoot = "${config.home.homeDirectory}/arr-stack";
  arrUsersCli = import ../users/arr-users-cli-home-manager.nix { inherit pkgs stackRoot; };
  arrStatusCli = import ../status/arr-status-cli-home-manager.nix { inherit pkgs stackRoot; };
  machineIdentityMapPath = ../../../../private-configuration/machines.nix;
  privateConfigPresent = builtins.pathExists machineIdentityMapPath;
  chiseMachineIdentity = lib.optionalAttrs privateConfigPresent (import machineIdentityMapPath).chise;
  chiseTailnetBindAddress = chiseMachineIdentity.tailscaleIp or "127.0.0.1";
  miwayomiWebCacheVersion = builtins.hashFile "sha256" ./miwayomi-interface-artwork.patch;
  miwayomiBuildContext = pkgs.runCommand "miwayomi-build-context" { } ''
    mkdir -p "$out"
    cp ${./miwayomi.Dockerfile} "$out/miwayomi.Dockerfile"
    cp ${./miwayomi-manga-input-initialization.patch} "$out/miwayomi-manga-input-initialization.patch"
    cp ${./miwayomi-watch-progress.patch} "$out/miwayomi-watch-progress.patch"
    cp ${./miwayomi-interface-artwork.patch} "$out/miwayomi-interface-artwork.patch"
  '';
  staticEnvironmentFileContents = builtins.readFile ./env;
  runtimeEnvironmentFileContents =
    (lib.removeSuffix "\n" staticEnvironmentFileContents)
    + "\n"
    + "ARR_BIND_ADDR=${chiseTailnetBindAddress}\n"
    + "MIWAYOMI_BUILD_CONTEXT=${miwayomiBuildContext}\n"
    + "MIWAYOMI_WEB_CACHE_VERSION=${miwayomiWebCacheVersion}\n"
    + "MIWAYOMI_GATEWAY_CONFIG_PATH=${./miwayomi-gateway.conf}\n";
  configServiceDirectories = [
    "qbittorrent"
    "prowlarr"
    "sonarr"
    "radarr"
    "bazarr"
    "jellyfin"
    "jellyseerr"
    "kavita"
    "miwayomi"
    "miwayomi-update-disabled"
    "flaresolverr"
  ];
  dataDirectories = [
    "torrents"
    "media/tv"
    "media/movies"
    "media/tv-private"
    "media/movies-private"
    "manga/mangas"
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
  home = {
    packages = [
      arrUsersCli
      arrStatusCli
    ];

    file = {
      "arr-stack/docker-compose.yml".source = ./docker-compose.yml;
      "arr-stack/.env".text = runtimeEnvironmentFileContents;
      "arr-stack/README.md".source = ./README.md;
    };

    activation.createArrStackPersistenceDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      ${makePersistenceDirectoriesCommand}
    '';
  };
}
