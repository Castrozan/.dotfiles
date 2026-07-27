{
  config,
  lib,
  pkgs,
  ...
}:
let
  jellyfinLibraryAccessProvisionerConfig = config.custom.jellyfinLibraryAccessProvisioner;
  arrUsersPackageDirectory = ../../../home/linux/arr-stack/scripts/arr_users;
in
{
  options.custom.jellyfinLibraryAccessProvisioner = {
    enable = lib.mkEnableOption "a root systemd oneshot that reconciles the Jellyfin private-library boundary at every rebuild: it creates any declared library that is missing and rewrites every non-administrator account's policy to EnableAllFolders=false with only the declared public libraries enabled, so a private library stays invisible to friends even if someone flips a checkbox in the Jellyfin dashboard or a new friend predates the boundary";

    jellyfinBaseUrl = lib.mkOption {
      type = lib.types.str;
      default = "http://127.0.0.1:8096";
      description = "Base URL the reconciler talks to Jellyfin on; the loopback publish of the jellyfin container, so the reconcile never depends on the tailnet being up.";
    };

    jellyfinApiKeySecretFile = lib.mkOption {
      type = lib.types.str;
      description = "Path to the agenix-decrypted Jellyfin admin API key the reconciler authenticates with; the same key the arr-users CLI reads, so both apply one policy source.";
    };

    libraryPathProviderUnits = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "Units that create the on-disk media directories the declared libraries point at, ordered before the reconcile. Jellyfin rejects a library whose path does not exist yet, so without this the first rebuild after declaring a library races the activation that creates its directory and the library is not created until the next rebuild.";
    };
  };

  config = lib.mkIf jellyfinLibraryAccessProvisionerConfig.enable {
    systemd.services.jellyfin-library-access-provisioner = {
      description = "Reconcile the Jellyfin private-library boundary from the committed friend policy";
      after = [
        "docker.service"
        "network-online.target"
      ]
      ++ jellyfinLibraryAccessProvisionerConfig.libraryPathProviderUnits;
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];
      environment = {
        ARR_USERS_JELLYFIN_BASE_URL = jellyfinLibraryAccessProvisionerConfig.jellyfinBaseUrl;
        ARR_USERS_JELLYFIN_API_KEY_FILE = jellyfinLibraryAccessProvisionerConfig.jellyfinApiKeySecretFile;
      };
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${pkgs.python3}/bin/python3 ${arrUsersPackageDirectory} sync";
      };
    };
  };
}
