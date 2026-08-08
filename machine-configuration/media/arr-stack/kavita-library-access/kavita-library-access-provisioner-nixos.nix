{
  config,
  lib,
  pkgs,
  ...
}:
let
  kavitaLibraryAccessProvisionerConfig = config.custom.kavitaLibraryAccessProvisioner;
  arrUsersPackageDirectory = ../users/scripts/arr_users;
in
{
  options.custom.kavitaLibraryAccessProvisioner = {
    enable = lib.mkEnableOption "reconciling every Kavita account onto the declared public library allowlist on each rebuild";

    kavitaBaseUrl = lib.mkOption {
      type = lib.types.str;
      default = "http://127.0.0.1:5000";
      description = "Base URL the provisioner reaches Kavita on, kept on loopback so the admin API key it exchanges for a bearer token never leaves the host.";
    };

    kavitaApiKeySecretFile = lib.mkOption {
      type = lib.types.str;
      description = "Path to the file holding the Kavita admin API key.";
    };

    publicLibraryNames = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "Kavita libraries every account may read. This is an allowlist, so a library absent from it is withheld from every account outside privilegedAccountUsernames and a newly created library stays private until it is declared here.";
    };

    privilegedAccountUsernames = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "Kavita accounts that read every library and keep their privileged roles. Every other account, whether declared as a friend or not, is pinned to publicLibraryNames and stripped of Admin, Promote and ChangeRestriction.";
    };

    friendAccountUsernames = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "The expected friend roster. It never widens access, because Kavita lets an invited friend choose their own username: it only lets the provisioner name, in its log, an account that registered without being declared.";
    };

    sourceFolderLibraryName = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Library whose folders track each immediate subdirectory of the source root rather than their shared parent, so Kavita reads a series name from the series directory instead of taking the extension's name as the publisher. Empty leaves the library folders alone.";
    };

    sourceRootHostPath = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Host path the provisioner enumerates to find the source directories. An absent or empty directory leaves the library folders alone.";
    };

    sourceRootContainerPath = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Path that same source root is mounted at inside the Kavita container, which is how Kavita must be told to spell the folders.";
    };

    libraryPathProviderUnits = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "Units that must have run before the reconcile, so Kavita is serving and the library paths it is pointed at already exist.";
    };
  };

  config = lib.mkIf kavitaLibraryAccessProvisionerConfig.enable {
    systemd.services.kavita-library-access-provisioner = {
      description = "Pin every Kavita account to the declared public library allowlist";
      after = [
        "docker.service"
        "network-online.target"
      ]
      ++ kavitaLibraryAccessProvisionerConfig.libraryPathProviderUnits;
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];
      environment = {
        ARR_USERS_KAVITA_BASE_URL = kavitaLibraryAccessProvisionerConfig.kavitaBaseUrl;
        ARR_USERS_KAVITA_API_KEY_FILE = kavitaLibraryAccessProvisionerConfig.kavitaApiKeySecretFile;
        ARR_USERS_KAVITA_PUBLIC_LIBRARIES = builtins.toJSON kavitaLibraryAccessProvisionerConfig.publicLibraryNames;
        ARR_USERS_KAVITA_PRIVILEGED_ACCOUNTS = builtins.toJSON kavitaLibraryAccessProvisionerConfig.privilegedAccountUsernames;
        ARR_USERS_KAVITA_FRIEND_ACCOUNTS = builtins.toJSON kavitaLibraryAccessProvisionerConfig.friendAccountUsernames;
        ARR_USERS_KAVITA_SOURCE_FOLDER_LIBRARY =
          kavitaLibraryAccessProvisionerConfig.sourceFolderLibraryName;
        ARR_USERS_KAVITA_SOURCE_ROOT_HOST_PATH = kavitaLibraryAccessProvisionerConfig.sourceRootHostPath;
        ARR_USERS_KAVITA_SOURCE_ROOT_CONTAINER_PATH =
          kavitaLibraryAccessProvisionerConfig.sourceRootContainerPath;
      };
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${pkgs.python3}/bin/python3 ${arrUsersPackageDirectory} sync-kavita-access";
      };
    };
  };
}
