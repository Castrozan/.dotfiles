{
  config,
  lib,
  pkgs,
  ...
}:
{
  systemd.services = {
    docker.unitConfig.RequiresMountsFor = [ "/home/zanoni/arr-stack/data" ];

    arr-stack-front-ends-compose = {
      preStart = ''
        ${pkgs.coreutils}/bin/chown -R 1000:1000 -- ${lib.escapeShellArg (builtins.dirOf config.custom.jellyseerrEmailNotifications.jellyseerrSettingsFile)}
      '';
      restartTriggers = [
        ../jellyseerr-notifications/Dockerfile
        ../jellyseerr-notifications/scripts/available_media_email.js
        ../jellyseerr-notifications/__tests__/test_available_media_email.cjs
      ];
    };

    jellyseerr-email-notifications.restartTriggers = [
      ../../../../secrets/credentials/media/jellyseerr-smtp-app-password.age
    ];

    arr-config-provisioner.restartTriggers = [
      ../../../../secrets/credentials/media/arr-qbittorrent-password.age
      ../../../../secrets/credentials/media/arr-radarr-password.age
      ../../../../secrets/credentials/media/arr-sonarr-password.age
      ../../../../secrets/credentials/media/arr-prowlarr-password.age
      ../../../../secrets/credentials/media/arr-samaritano-indexer-apikey.age
    ];

    bazarr-auth-provisioner.restartTriggers = [
      ../../../../secrets/credentials/media/arr-bazarr-password.age
    ];

    jellyfin-library-access-provisioner.restartTriggers = [
      ../../../../secrets/credentials/media/jellyfin-admin-api-key.age
    ];

    miwayomi-extension-repositories.restartTriggers = [
      ../../../../secrets/credentials/media/suwayomi-extension-repositories.age
    ];

    jellyseerr-private-request-routing-provisioner.restartTriggers = [
      ../../../../secrets/credentials/media/jellyfin-admin-api-key.age
    ];

    jellyseerr-account-permission-provisioner.restartTriggers = [
      ../../../../secrets/credentials/media/jellyfin-admin-api-key.age
    ];
  };
}
