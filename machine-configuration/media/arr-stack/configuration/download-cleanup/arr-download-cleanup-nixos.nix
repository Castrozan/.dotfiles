{
  config,
  lib,
  pkgs,
  username,
  ...
}:
let
  cleanupConfig = config.custom.arrDownloadCleanup;
  packageDirectory = ./scripts;
  pythonCommand = "${pkgs.python3}/bin/python3 -m download_cleanup";
in
{
  options.custom.arrDownloadCleanup = {
    enable = lib.mkEnableOption "clean up torrent payloads after native Radarr and Sonarr media deletion events";
    stackHomeDirectory = lib.mkOption {
      type = lib.types.str;
      description = "Arr-stack directory containing runtime application config and the mounted data drive.";
    };
    qbittorrentPasswordSecretFile = lib.mkOption {
      type = lib.types.str;
      description = "qBittorrent password supplied through systemd credentials and used to authenticate native webhooks.";
    };
    jellyfinApiKeySecretFile = lib.mkOption {
      type = lib.types.str;
      description = "Jellyfin API key supplied through systemd credentials for library refresh after cleanup.";
    };
  };

  config = lib.mkIf cleanupConfig.enable {
    systemd.services.arr-download-cleanup = {
      description = "Remove exact torrent hashes and payloads after file-inclusive media deletions";
      after = [
        "docker.service"
        "network-online.target"
      ];
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];
      unitConfig.RequiresMountsFor = [ "${cleanupConfig.stackHomeDirectory}/data" ];
      environment = {
        PYTHONPATH = toString packageDirectory;
        ARR_CLEANUP_STACK_HOME = cleanupConfig.stackHomeDirectory;
      };
      serviceConfig = {
        Type = "exec";
        User = username;
        StateDirectory = "arr-download-cleanup";
        StateDirectoryMode = "0700";
        LoadCredential = [
          "qbittorrent-password:${cleanupConfig.qbittorrentPasswordSecretFile}"
          "jellyfin-api-key:${cleanupConfig.jellyfinApiKeySecretFile}"
        ];
        ExecStartPre = "${pythonCommand} bootstrap";
        ExecStart = pythonCommand;
        Restart = "on-failure";
        RestartSec = 10;
        TimeoutStartSec = 120;
        UMask = "0077";
        NoNewPrivileges = true;
        ProtectSystem = "strict";
        ProtectHome = "read-only";
        PrivateTmp = true;
        PrivateDevices = true;
        ProtectKernelTunables = true;
        ProtectKernelModules = true;
        ProtectControlGroups = true;
        RestrictAddressFamilies = [
          "AF_INET"
          "AF_UNIX"
        ];
        MemoryMax = "128M";
        CPUQuota = "10%";
      };
    };

    systemd.services.arr-config-provisioner = {
      after = [ "arr-download-cleanup.service" ];
      wants = [ "arr-download-cleanup.service" ];
    };

    networking.firewall.interfaces."br-+".allowedTCPPorts = [ 8789 ];
  };
}
