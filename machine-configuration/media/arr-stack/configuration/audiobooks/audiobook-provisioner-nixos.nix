{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.custom.audiobookProvisioner;
in
{
  options.custom.audiobookProvisioner = {
    enable = lib.mkEnableOption "persistent audiobook account and integration provisioning";
    username = lib.mkOption {
      type = lib.types.str;
      description = "Administrator login for the audiobook applications.";
    };
    downloadUsername = lib.mkOption {
      type = lib.types.str;
      default = config.custom.arrConfigProvisioner.qbittorrentUsername;
      description = "Existing download-client login, independent from audiobook app accounts.";
    };
    passwordFile = lib.mkOption {
      type = lib.types.str;
      description = "Runtime agenix password file, never copied into the Nix store.";
    };
    prowlarrConfigFile = lib.mkOption {
      type = lib.types.str;
      description = "Runtime Prowlarr config.xml containing its API key.";
    };
    prowlarrBaseUrl = lib.mkOption {
      type = lib.types.str;
      description = "Host-reachable Prowlarr API URL.";
    };
    audiobookshelfBaseUrl = lib.mkOption {
      type = lib.types.str;
      description = "Host-reachable Audiobookshelf API URL.";
    };
    readmeabookBaseUrl = lib.mkOption {
      type = lib.types.str;
      description = "Host-reachable ReadMeABook API URL.";
    };
  };
  config = lib.mkIf cfg.enable {
    systemd.services.arr-audiobook-provisioner = {
      description = "Provision audiobook accounts, library and download integrations";
      after = [
        "arr-stack-front-ends-compose.service"
        "arr-config-provisioner.service"
        "agenix.service"
        "network-online.target"
      ];
      wants = [
        "arr-stack-front-ends-compose.service"
        "arr-config-provisioner.service"
        "network-online.target"
      ];
      wantedBy = [ "multi-user.target" ];
      environment = {
        AUDIOBOOK_USERNAME = cfg.username;
        QBITTORRENT_USERNAME = cfg.downloadUsername;
        AUDIOBOOK_PASSWORD_FILE = cfg.passwordFile;
        PROWLARR_CONFIG_FILE = cfg.prowlarrConfigFile;
        PROWLARR_BASE_URL = cfg.prowlarrBaseUrl;
        AUDIOBOOKSHELF_BASE_URL = cfg.audiobookshelfBaseUrl;
        READMEABOOK_BASE_URL = cfg.readmeabookBaseUrl;
      };
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        ExecStart = "${pkgs.python3}/bin/python3 ${./scripts}/provision.py";
        StateDirectory = "arr-audiobooks";
        StateDirectoryMode = "0700";
        UMask = "0077";
        TimeoutStartSec = 900;
        Restart = "on-failure";
        RestartSec = 60;
        NoNewPrivileges = true;
        ProtectSystem = "strict";
        ProtectHome = "read-only";
        PrivateTmp = true;
      };
    };
  };
}
