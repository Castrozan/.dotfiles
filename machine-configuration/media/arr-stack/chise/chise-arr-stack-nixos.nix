{ config, ... }:
{
  imports = [ ./cloudflare-origins ];

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
        frontEndServices = [
          "jellyfin"
          "jellyseerr"
          "kavita"
          "miwayomi"
          "flaresolverr"
        ];
      };
    };

    miwayomi = {
      enable = true;
      stackHomeDirectory = "/home/zanoni/arr-stack";
      baseUrl = "http://arr:4568";
      repositoryListSecretFile = config.age.secrets."suwayomi-extension-repositories".path;
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

    kavitaLibraryAccessProvisioner = {
      enable = true;
      kavitaApiKeySecretFile = config.age.secrets."kavita-admin-api-key".path;
      publicLibraryNames = [ "Manga" ];
      privilegedAccountUsernames = [ "zanoni" ];
      friendAccountUsernames = [
        "joshen"
        "rogerio"
        "Xamitos"
      ];
      sourceFolderLibraryName = "Manga";
      sourceRootHostPath = "/home/zanoni/arr-stack/data/manga/mangas";
      sourceRootContainerPath = "/manga";
      libraryPathProviderUnits = [ "docker.service" ];
    };

    bazarrAuthProvisioner = {
      enable = true;
      configFile = "/home/zanoni/arr-stack/config/bazarr/config/config.yaml";
      containerName = "arr-bazarr";
      loginUsername = "lucas";
      passwordSecretFile = config.age.secrets."arr-bazarr-password".path;
    };
  };

  systemd.services = {
    docker.unitConfig.RequiresMountsFor = [ "/home/zanoni/arr-stack/data" ];

    jellyseerr-email-notifications.restartTriggers = [
      ../../../../secrets/credentials/jellyseerr-smtp-app-password.age
    ];

    arr-config-provisioner.restartTriggers = [
      ../../../../secrets/credentials/arr-qbittorrent-password.age
      ../../../../secrets/credentials/arr-radarr-password.age
      ../../../../secrets/credentials/arr-sonarr-password.age
      ../../../../secrets/credentials/arr-prowlarr-password.age
      ../../../../secrets/credentials/arr-samaritano-indexer-apikey.age
    ];

    bazarr-auth-provisioner.restartTriggers = [
      ../../../../secrets/credentials/arr-bazarr-password.age
    ];

    jellyfin-library-access-provisioner.restartTriggers = [
      ../../../../secrets/credentials/jellyfin-admin-api-key.age
    ];

    kavita-library-access-provisioner.restartTriggers = [
      ../../../../secrets/credentials/kavita-admin-api-key.age
    ];

    miwayomi-extension-repositories.restartTriggers = [
      ../../../../secrets/credentials/suwayomi-extension-repositories.age
    ];

    jellyseerr-private-request-routing-provisioner.restartTriggers = [
      ../../../../secrets/credentials/jellyfin-admin-api-key.age
    ];

    jellyseerr-account-permission-provisioner.restartTriggers = [
      ../../../../secrets/credentials/jellyfin-admin-api-key.age
    ];
  };
}
