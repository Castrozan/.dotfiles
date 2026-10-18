{
  config,
  inputs,
  lib,
  ...
}:
let
  bindAddress = import ../../../../media/tailnet-bind-address.nix { inherit lib; };
  secret = name: {
    file = config.age.secrets.${name}.path;
    source = config.age.secrets.${name}.file;
  };
in
{
  imports = [
    inputs.arr-stack.nixosModules.default
    ./arr-stack-origins.nix
  ];

  services.arrStack = {
    enable = true;
    user = "zanoni";
    userId = 1000;
    groupId = 100;
    directory = "/home/zanoni/arr-stack";
    inherit bindAddress;
    loginUsername = "lucas";
    hardwareAcceleration = "nvidia";
    containerCgroupParent = "media-containers.slice";
    dataDeviceUnit = "dev-disk-by\\x2dlabel-arr\\x2ddata.device";
    dataMountUnit = "home-zanoni-arr\\x2dstack-data.mount";
    publicRequesterUsername = "lucas";
    jellyfinPublicUrl = "https://watch.lucaszanoni.com";
    readmeabookPublicUrl = "https://readmeabook.lucaszanoni.com";
    accounts = {
      privateLibraryAccounts = [
        "private-requests"
        "jellyseerr"
      ];
      administratorAccounts = [ "jellyseerr" ];
      advancedRequestAccounts = [
        "lucas"
        "rogerio"
      ];
    };
    smtp = {
      username = "castro.lucas290@gmail.com";
      sender = "castro.lucas290@gmail.com";
      recipient = "castro.lucas290@gmail.com";
    };
    removedExtensionPackages = [
      "eu.kanade.tachiyomi.animeextension.en.animepahe"
      "eu.kanade.tachiyomi.animeextension.en.kayoanime"
      "eu.kanade.tachiyomi.extension.en.bakkin"
    ];
    secrets = {
      jellyfinApiKey = secret "jellyfin-admin-api-key";
      qbittorrentPassword = secret "arr-qbittorrent-password";
      radarrPassword = secret "arr-radarr-password";
      sonarrPassword = secret "arr-sonarr-password";
      prowlarrPassword = secret "arr-prowlarr-password";
      bazarrPassword = secret "arr-bazarr-password";
      samaritanoApiKey = secret "arr-samaritano-indexer-apikey";
      smtpPassword = secret "jellyseerr-smtp-app-password";
      extensionRepositories = secret "suwayomi-extension-repositories";
      audiobookshelfPassword = secret "arr-audiobookshelf-password";
      readmeabookPassword = secret "arr-readmeabook-password";
    };
  };

  networking.hosts = lib.optionalAttrs (bindAddress != "127.0.0.1") {
    "${bindAddress}" = [ "arr" ];
  };

  custom.stremioStreamingServer.streamCacheDirectory = "${config.services.arrStack.directory}/data/stremio-cache";
}
