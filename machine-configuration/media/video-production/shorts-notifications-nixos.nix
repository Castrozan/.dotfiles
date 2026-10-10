{
  config,
  pkgs,
  username,
  ...
}:
let
  notifier = pkgs.writeShellScript "shorts-publication-email" ''
    export PYTHONPATH=${./shorts-automation/scripts}
    exec ${pkgs.python312}/bin/python3 -m shorts_notifications
  '';
in
{
  systemd.services.shorts-publication-email = {
    description = "Email verified Shorts links with durable delivery deduplication";
    environment.SHORTS_STATE_DIRECTORY = "${config.users.users.${username}.home}/clawde/shorts";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = notifier;
      StateDirectory = "shorts-publication-email";
      StateDirectoryMode = "0700";
      LoadCredential = "smtp-password:${config.age.secrets.jellyseerr-smtp-app-password.path}";
      UMask = "0077";
      TimeoutStartSec = "4min";
      MemoryMax = "128M";
      Nice = 10;
      NoNewPrivileges = true;
      PrivateTmp = true;
      ProtectSystem = "strict";
      ProtectHome = "read-only";
      CapabilityBoundingSet = [ "CAP_DAC_READ_SEARCH" ];
      RestrictAddressFamilies = [
        "AF_INET"
        "AF_INET6"
      ];
    };
  };
  systemd.timers.shorts-publication-email = {
    description = "Deliver newly published Shorts and retry unsent email";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "2min";
      OnUnitInactiveSec = "5min";
      AccuracySec = "15s";
    };
  };
}
