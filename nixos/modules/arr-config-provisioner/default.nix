{
  config,
  lib,
  pkgs,
  ...
}:
let
  arrConfigProvisionerConfig = config.custom.arrConfigProvisioner;
  provisionerPackageDirectory = ./scripts/arr_config_provisioner;
  desiredStateDirectory = ./desired-state;
  stackHome = arrConfigProvisionerConfig.stackHomeDirectory;
in
{
  options.custom.arrConfigProvisioner = {
    enable = lib.mkEnableOption "a root systemd oneshot that reconstructs the arr-stack app config (radarr/sonarr/prowlarr download clients, root folders, custom formats and indexers) declaratively by idempotently upserting committed desired-state JSON into each app's API at rebuild, so a wiped or lost config directory is rebuilt from the repo instead of from an off-host backup; the only real secrets (the qBittorrent password and the private indexer key) are injected from agenix at runtime";

    stackHomeDirectory = lib.mkOption {
      type = lib.types.str;
      description = "Absolute path to the arr-stack home directory holding .env and config/<app>/config.xml; the provisioner reads the build-generated bind address and each app's on-disk API key from underneath it, exactly like the on-demand supervisor.";
    };

    bindAddressKey = lib.mkOption {
      type = lib.types.str;
      default = "ARR_BIND_ADDR";
      description = "The .env key the provisioner reads at runtime to learn the tailnet address the *arr web UIs listen on, so the tailscale IP stays out of the nix source and lives only in the build-generated .env.";
    };

    qbittorrentPasswordSecretFile = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Path to the agenix-decrypted qBittorrent WebUI password substituted into the @QBITTORRENT_PASSWORD@ placeholder of the download-client desired state; when unset or the file is absent the download clients are skipped rather than provisioned with an empty password.";
    };

    samaritanoApiKeySecretFile = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Path to the agenix-decrypted private-indexer key substituted into the @SAMARITANO_APIKEY@ placeholder of the indexer desired state; when unset or the file is absent the private indexer is skipped while the public indexers still provision.";
    };

    loginUsername = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Web-UI login username set as the Forms-auth account on radarr/sonarr/prowlarr; combined with each app's password secret it gives one owner login per app. When empty the host-login step is skipped, leaving each app's existing auth untouched.";
    };

    radarrPasswordSecretFile = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Path to the agenix-decrypted radarr web-UI login password; radarr's Forms auth is left untouched when unset so a missing secret never locks the app open with an empty password.";
    };

    sonarrPasswordSecretFile = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Path to the agenix-decrypted sonarr web-UI login password; sonarr's Forms auth is left untouched when unset.";
    };

    prowlarrPasswordSecretFile = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Path to the agenix-decrypted prowlarr web-UI login password; prowlarr's Forms auth is left untouched when unset.";
    };
  };

  config = lib.mkIf arrConfigProvisionerConfig.enable {
    systemd.services.arr-config-provisioner = {
      description = "Reconstruct the arr-stack app config declaratively from committed desired state";
      after = [
        "docker.service"
        "network-online.target"
      ];
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];
      environment = {
        ARR_PROVISIONER_ENV_FILE = "${stackHome}/.env";
        ARR_BIND_ADDRESS_KEY = arrConfigProvisionerConfig.bindAddressKey;
        ARR_PROVISIONER_CONFIG_ROOT = "${stackHome}/config";
        ARR_PROVISIONER_DESIRED_STATE_DIR = "${desiredStateDirectory}";
        ARR_PROVISIONER_QBITTORRENT_PASSWORD_FILE =
          arrConfigProvisionerConfig.qbittorrentPasswordSecretFile;
        ARR_PROVISIONER_SAMARITANO_APIKEY_FILE = arrConfigProvisionerConfig.samaritanoApiKeySecretFile;
        ARR_PROVISIONER_LOGIN_USERNAME = arrConfigProvisionerConfig.loginUsername;
        ARR_PROVISIONER_RADARR_PASSWORD_FILE = arrConfigProvisionerConfig.radarrPasswordSecretFile;
        ARR_PROVISIONER_SONARR_PASSWORD_FILE = arrConfigProvisionerConfig.sonarrPasswordSecretFile;
        ARR_PROVISIONER_PROWLARR_PASSWORD_FILE = arrConfigProvisionerConfig.prowlarrPasswordSecretFile;
      };
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${pkgs.python3}/bin/python3 ${provisionerPackageDirectory}";
      };
    };
  };
}
