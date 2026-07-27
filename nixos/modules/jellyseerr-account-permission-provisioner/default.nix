{
  config,
  lib,
  pkgs,
  ...
}:
let
  accountPermissionConfig = config.custom.jellyseerrAccountPermissionProvisioner;
  arrUsersPackageDirectory = ../../../home/linux/arr-stack/scripts/arr_users;
in
{
  options.custom.jellyseerrAccountPermissionProvisioner = {
    enable = lib.mkEnableOption "a root systemd oneshot that pins every Jellyseerr account except the declared administrator to request-and-auto-approve, so no request from anyone ever waits on an approval and no account but the administrator can read another account's request list. Jellyseerr grants an account holding admin or manage-requests a view of every request by title, so leaving the daily-driver account privileged would expose the private account's requests there even though the private libraries themselves stay hidden";

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
      description = "Path to the Jellyseerr settings.json the reconciler reads its admin API key out of; the user permission endpoints are admin-gated. Jellyseerr resolves that key to its owner account, so the reconcile keeps working no matter which permissions the human accounts hold.";
    };

    orderedBeforeUnits = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "Units ordered after this reconcile. The request-routing reconcile refuses to run against a privileged routing account, so settling permissions first keeps it from failing on a state this unit is about to correct.";
    };
  };

  config = lib.mkIf accountPermissionConfig.enable {
    systemd.services.jellyseerr-account-permission-provisioner = {
      description = "Pin every Jellyseerr account to request-and-auto-approve except the declared administrator";
      after = [
        "docker.service"
        "network-online.target"
      ];
      before = accountPermissionConfig.orderedBeforeUnits;
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];
      environment = {
        ARR_USERS_JELLYFIN_BASE_URL = accountPermissionConfig.jellyfinBaseUrl;
        ARR_USERS_JELLYFIN_API_KEY_FILE = accountPermissionConfig.jellyfinApiKeySecretFile;
        ARR_USERS_JELLYSEERR_BASE_URL = accountPermissionConfig.jellyseerrBaseUrl;
        ARR_USERS_JELLYSEERR_SETTINGS_FILE = accountPermissionConfig.jellyseerrSettingsFile;
      };
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${pkgs.python3}/bin/python3 ${arrUsersPackageDirectory} sync-account-permissions";
      };
    };
  };
}
