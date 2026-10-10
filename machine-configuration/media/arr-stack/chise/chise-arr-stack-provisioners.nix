{ config, ... }:
{
  custom = {
    arrMediaTailscaleFunnel = {
      enable = true;
      funnels = [ ];
    };

    arrStackOnDemandSupervisor = {
      enable = true;
      stackHomeDirectory = "/home/zanoni/arr-stack";
      keepChainAlwaysOn = true;
      diskGuard = {
        path = "/home/zanoni/arr-stack/data";
        alertSmtpUsername = "castro.lucas290@gmail.com";
        alertEmailSender = "castro.lucas290@gmail.com";
        alertEmailRecipient = "castro.lucas290@gmail.com";
        alertAppPasswordSecretFile = config.age.secrets."jellyseerr-smtp-app-password".path;
      };
      mountGuard = {
        enable = true;
        dataDeviceUnit = "dev-disk-by\\x2dlabel-arr\\x2ddata.device";
        dataMountUnit = "home-zanoni-arr\\x2dstack-data.mount";
        composeDeclarationProviderUnits = [ "home-manager-zanoni.service" ];
        composeApplicatorPredecessorUnits = [ "miwayomi-compose.service" ];
        frontEndServices = [
          "jellyfin"
          "jellyseerr"
          "suwayomi"
          "miwayomi"
          "miwayomi-gateway"
          "flaresolverr"
          "audiobookshelf"
          "readmeabook"
        ];
      };
    };

    stremioStreamingServer.streamCacheDirectory = "/home/zanoni/arr-stack/data/stremio-cache";

    miwayomi = {
      enable = true;
      stackHomeDirectory = "/home/zanoni/arr-stack";
      baseUrl = "http://arr:4568";
      repositoryListSecretFile = config.age.secrets."suwayomi-extension-repositories".path;
      removedExtensionPackages = [
        "eu.kanade.tachiyomi.animeextension.en.animepahe"
        "eu.kanade.tachiyomi.animeextension.en.kayoanime"
        "eu.kanade.tachiyomi.extension.en.bakkin"
      ];
      composePredecessorUnits = [ "arr-stack-drive-guard.service" ];
    };

    jellyseerrEmailNotifications = {
      enable = true;
      jellyseerrSettingsFile = "/home/zanoni/arr-stack/config/jellyseerr/settings.json";
      senderAddress = "castro.lucas290@gmail.com";
      smtpUsername = "castro.lucas290@gmail.com";
      appPasswordSecretFile = config.age.secrets."jellyseerr-smtp-app-password".path;
      notificationTypesBitmask = 142;
    };

    arrConfigProvisioner = {
      enable = true;
      stackHomeDirectory = "/home/zanoni/arr-stack";
      qbittorrentPasswordSecretFile = config.age.secrets."arr-qbittorrent-password".path;
      samaritanoApiKeySecretFile = config.age.secrets."arr-samaritano-indexer-apikey".path;
      loginUsername = "lucas";
      radarrPasswordSecretFile = config.age.secrets."arr-radarr-password".path;
      sonarrPasswordSecretFile = config.age.secrets."arr-sonarr-password".path;
      prowlarrPasswordSecretFile = config.age.secrets."arr-prowlarr-password".path;
    };

    arrDownloadCleanup = {
      enable = true;
      stackHomeDirectory = "/home/zanoni/arr-stack";
      qbittorrentPasswordSecretFile = config.age.secrets."arr-qbittorrent-password".path;
      jellyfinApiKeySecretFile = config.age.secrets."jellyfin-admin-api-key".path;
    };

    jellyfinLibraryAccessProvisioner = {
      enable = true;
      jellyfinApiKeySecretFile = config.age.secrets."jellyfin-admin-api-key".path;
      libraryPathProviderUnits = [ "home-manager-zanoni.service" ];
    };

    jellyfinSubtitleExtractionWarmer = {
      enable = true;
      jellyfinApiKeySecretFile = config.age.secrets."jellyfin-admin-api-key".path;
      jellyfinDataDirectory = "/home/zanoni/arr-stack/config/jellyfin/data/data";
    };

    jellyseerrAccountPermissionProvisioner = {
      enable = true;
      jellyfinApiKeySecretFile = config.age.secrets."jellyfin-admin-api-key".path;
      jellyseerrSettingsFile = "/home/zanoni/arr-stack/config/jellyseerr/settings.json";
      orderedBeforeUnits = [ "jellyseerr-private-request-routing-provisioner.service" ];
    };

    jellyseerrPrivateRequestRoutingProvisioner = {
      enable = true;
      jellyfinApiKeySecretFile = config.age.secrets."jellyfin-admin-api-key".path;
      jellyseerrSettingsFile = "/home/zanoni/arr-stack/config/jellyseerr/settings.json";
      rootFolderProviderUnits = [ "arr-config-provisioner.service" ];
    };

    bazarrAuthProvisioner = {
      enable = true;
      configFile = "/home/zanoni/arr-stack/config/bazarr/config/config.yaml";
      containerName = "arr-bazarr";
      loginUsername = "lucas";
      passwordSecretFile = config.age.secrets."arr-bazarr-password".path;
    };
  };
}
