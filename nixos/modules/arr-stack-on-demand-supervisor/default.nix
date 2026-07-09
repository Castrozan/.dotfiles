{
  config,
  lib,
  pkgs,
  ...
}:
let
  arrStackOnDemandSupervisorConfig = config.custom.arrStackOnDemandSupervisor;
  diskGuardConfig = arrStackOnDemandSupervisorConfig.diskGuard;
  supervisorPackageDirectory = ./scripts/on_demand_supervisor;
  stateDirectoryName = "arr-stack-on-demand-supervisor";
  stackHome = arrStackOnDemandSupervisorConfig.stackHomeDirectory;
  diskGuardPath = if diskGuardConfig.path == "" then stackHome else diskGuardConfig.path;
in
{
  imports = [ ./options.nix ];

  config = lib.mkIf arrStackOnDemandSupervisorConfig.enable {
    systemd.services.arr-stack-on-demand-supervisor = {
      description = "Bring the arr-stack download chain up on demand and stop it when idle";
      after = [
        "docker.service"
        "network-online.target"
      ];
      wants = [ "network-online.target" ];
      path = [ pkgs.docker ];
      environment = {
        ARR_COMPOSE_FILE = "${stackHome}/docker-compose.yml";
        ARR_ENV_FILE = "${stackHome}/.env";
        ARR_PROJECT_DIRECTORY = stackHome;
        ARR_COMPOSE_PROJECT = arrStackOnDemandSupervisorConfig.composeProjectName;
        DOCKER_COMPOSE_BIN = "${pkgs.docker-compose}/bin/docker-compose";
        ARR_ON_DEMAND_SERVICES = lib.concatStringsSep " " arrStackOnDemandSupervisorConfig.onDemandServices;
        ARR_IDLE_GRACE_SECONDS = toString arrStackOnDemandSupervisorConfig.idleGraceSeconds;
        ARR_KEEP_CHAIN_ALWAYS_ON =
          if arrStackOnDemandSupervisorConfig.keepChainAlwaysOn then "true" else "false";
        ARR_RECENT_PENDING_WINDOW_SECONDS = toString arrStackOnDemandSupervisorConfig.recentPendingWindowSeconds;
        ARR_STATE_FILE = "/var/lib/${stateDirectoryName}/last-active-epoch";
        ARR_BIND_ADDRESS_KEY = arrStackOnDemandSupervisorConfig.bindAddressKey;
        JELLYSEERR_URL = arrStackOnDemandSupervisorConfig.jellyseerrUrl;
        JELLYSEERR_SETTINGS_FILE = "${stackHome}/config/jellyseerr/settings.json";
        RADARR_PORT = arrStackOnDemandSupervisorConfig.radarrPort;
        RADARR_CONFIG_FILE = "${stackHome}/config/radarr/config.xml";
        SONARR_PORT = arrStackOnDemandSupervisorConfig.sonarrPort;
        SONARR_CONFIG_FILE = "${stackHome}/config/sonarr/config.xml";
        ARR_DISK_GUARD_PATH = diskGuardPath;
        ARR_DISK_GUARD_WARNING_GIGABYTES = toString diskGuardConfig.warningFreeGigabytes;
        ARR_DISK_GUARD_CRITICAL_GIGABYTES = toString diskGuardConfig.criticalFreeGigabytes;
        ARR_DISK_GUARD_FILL_SERVICE = diskGuardConfig.fillService;
        ARR_DISK_GUARD_CRITICAL_REMINDER_SECONDS = toString diskGuardConfig.criticalReminderSeconds;
        ARR_DISK_GUARD_ALERT_STATE_FILE = "/var/lib/${stateDirectoryName}/disk-guard-alert-state.json";
        ARR_DISK_ALERT_SMTP_HOST = diskGuardConfig.alertSmtpHost;
        ARR_DISK_ALERT_SMTP_PORT = toString diskGuardConfig.alertSmtpPort;
        ARR_DISK_ALERT_SMTP_USERNAME = diskGuardConfig.alertSmtpUsername;
        ARR_DISK_ALERT_EMAIL_SENDER = diskGuardConfig.alertEmailSender;
        ARR_DISK_ALERT_EMAIL_RECIPIENT = diskGuardConfig.alertEmailRecipient;
        ARR_DISK_ALERT_APP_PASSWORD_FILE = diskGuardConfig.alertAppPasswordSecretFile;
      };
      serviceConfig = {
        Type = "oneshot";
        StateDirectory = stateDirectoryName;
        ExecStart = "${pkgs.python3}/bin/python3 ${supervisorPackageDirectory}";
      };
    };

    systemd.timers.arr-stack-on-demand-supervisor = {
      description = "Poll arr-stack demand and idle state on a fixed interval";
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnBootSec = "5min";
        OnUnitActiveSec = "${toString arrStackOnDemandSupervisorConfig.pollIntervalSeconds}s";
        Unit = "arr-stack-on-demand-supervisor.service";
      };
    };
  };
}
