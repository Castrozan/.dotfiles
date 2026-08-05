{
  config,
  lib,
  pkgs,
  ...
}:
let
  privateRequestRoutingConfig = config.custom.jellyseerrPrivateRequestRoutingProvisioner;
  arrUsersPackageDirectory = ../users/scripts/arr_users;
in
{
  options.custom.jellyseerrPrivateRequestRoutingProvisioner = {
    enable = lib.mkEnableOption "a root systemd oneshot that reconciles the Jellyseerr override rules sending every request made by the declared private-requests account to a private root folder, so requesting privately is a matter of which account you log in as rather than remembering to add the title in Radarr or Sonarr by hand. Jellyseerr skips override rules entirely for any account holding admin or manage-requests, so the routed account must stay an ordinary requester or its requests silently land in public view";

    jellyfinBaseUrl = lib.mkOption {
      type = lib.types.str;
      default = "http://127.0.0.1:8096";
      description = "Base URL for Jellyfin; the arr-users context builds both service clients even though this reconcile only writes to Jellyseerr.";
    };

    jellyfinApiKeySecretFile = lib.mkOption {
      type = lib.types.str;
      description = "Path to the agenix-decrypted Jellyfin admin API key the arr-users context requires.";
    };

    jellyseerrBaseUrl = lib.mkOption {
      type = lib.types.str;
      default = "http://127.0.0.1:5055";
      description = "Base URL the reconciler talks to Jellyseerr on; the loopback publish of the jellyseerr container, so the reconcile never depends on the tailnet being up.";
    };

    jellyseerrSettingsFile = lib.mkOption {
      type = lib.types.str;
      description = "Path to the Jellyseerr settings.json the reconciler reads its admin API key out of; the override rule endpoints are admin-gated.";
    };

    rootFolderProviderUnits = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "Units that register the private root folders in Radarr and Sonarr, ordered before this reconcile. A rule naming a root folder the *arr app does not know about is written happily and only fails later, at the moment a request is grabbed.";
    };
  };

  config = lib.mkIf privateRequestRoutingConfig.enable {
    systemd.services.jellyseerr-private-request-routing-provisioner = {
      description = "Reconcile the Jellyseerr override rules that route private requests";
      after = [
        "docker.service"
        "network-online.target"
      ]
      ++ privateRequestRoutingConfig.rootFolderProviderUnits;
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];
      environment = {
        ARR_USERS_JELLYFIN_BASE_URL = privateRequestRoutingConfig.jellyfinBaseUrl;
        ARR_USERS_JELLYFIN_API_KEY_FILE = privateRequestRoutingConfig.jellyfinApiKeySecretFile;
        ARR_USERS_JELLYSEERR_BASE_URL = privateRequestRoutingConfig.jellyseerrBaseUrl;
        ARR_USERS_JELLYSEERR_SETTINGS_FILE = privateRequestRoutingConfig.jellyseerrSettingsFile;
      };
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${pkgs.python3}/bin/python3 ${arrUsersPackageDirectory} sync-request-routing";
      };
    };
  };
}
