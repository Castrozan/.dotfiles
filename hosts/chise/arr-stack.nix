{ config, ... }:
{
  custom = {
    arrMediaLoginRateLimitProxy = {
      enable = true;
      origins = [
        {
          listenPort = 9443;
          upstreamUrl = "http://127.0.0.1:8096";
          loginLocationRegexes = [ "^/Users/AuthenticateByName" ];
        }
        {
          listenPort = 9444;
          upstreamUrl = "http://127.0.0.1:5055";
          loginLocationRegexes = [ "^/api/v1/auth/(jellyfin|plex|local)" ];
        }
      ];
    };

    arrMediaTailscaleFunnel = {
      enable = true;
      funnels = [
        {
          publicHttpsPort = 443;
          loopbackUrl = "http://127.0.0.1:9443";
        }
        {
          publicHttpsPort = 8443;
          loopbackUrl = "http://127.0.0.1:9444";
        }
      ];
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
        ];
      };
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
  };

  systemd.services = {
    docker.unitConfig.RequiresMountsFor = [ "/home/zanoni/arr-stack/data" ];

    arr-media-tailscale-funnel = {
      after = [ "nginx.service" ];
      requires = [ "nginx.service" ];
    };

    jellyseerr-email-notifications.restartTriggers = [
      ../../secrets/credentials/jellyseerr-smtp-app-password.age
    ];

    arr-config-provisioner.restartTriggers = [
      ../../secrets/credentials/arr-qbittorrent-password.age
      ../../secrets/credentials/arr-radarr-password.age
      ../../secrets/credentials/arr-sonarr-password.age
      ../../secrets/credentials/arr-prowlarr-password.age
      ../../secrets/credentials/arr-samaritano-indexer-apikey.age
    ];
  };
}
