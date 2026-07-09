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
      };
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${pkgs.python3}/bin/python3 ${provisionerPackageDirectory}";
      };
    };
  };
}
