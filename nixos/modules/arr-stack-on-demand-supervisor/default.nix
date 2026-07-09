{
  config,
  lib,
  pkgs,
  ...
}:
let
  arrStackOnDemandSupervisorConfig = config.custom.arrStackOnDemandSupervisor;
  supervisorPackageDirectory = ./scripts/on_demand_supervisor;
  stateDirectoryName = "arr-stack-on-demand-supervisor";
  stackHome = arrStackOnDemandSupervisorConfig.stackHomeDirectory;
in
{
  options.custom.arrStackOnDemandSupervisor = {
    enable = lib.mkEnableOption "a root systemd timer that brings the arr-stack download chain (radarr/sonarr/prowlarr/qbittorrent/bazarr) up on demand when a Jellyseerr request needs fulfilling, keeps it up while a download queue is active, and stops it after an idle grace, so the download chain runs only while there is work instead of 24/7, without touching the always-on jellyfin/jellyseerr front ends";

    stackHomeDirectory = lib.mkOption {
      type = lib.types.str;
      description = "Absolute path to the arr-stack home directory holding docker-compose.yml, .env and config/, e.g. /home/zanoni/arr-stack; the supervisor reads the compose project, the generated .env bind address and each app's on-disk API key from underneath it.";
    };

    composeProjectName = lib.mkOption {
      type = lib.types.str;
      default = "arr-stack";
      description = "The docker compose project name the on-demand services live under, matching the name declared in docker-compose.yml.";
    };

    onDemandServices = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [
        "radarr"
        "sonarr"
        "prowlarr"
        "qbittorrent"
        "bazarr"
      ];
      description = "The download-chain compose services brought up on demand and stopped when idle; excludes the always-on jellyfin/jellyseerr front ends, and since Jellyseerr requests are movie/TV only it leaves lidarr/readarr down.";
    };

    idleGraceSeconds = lib.mkOption {
      type = lib.types.int;
      default = 1200;
      description = "How long the download chain may sit with no active download queue and no actionable request before the supervisor stops it, covering post-download import and a brief search with no immediate result without flapping.";
    };

    pollIntervalSeconds = lib.mkOption {
      type = lib.types.int;
      default = 180;
      description = "How often the supervisor re-evaluates demand and idle state; media requests tolerate a few minutes of start latency so a short poll is unnecessary.";
    };

    recentPendingWindowSeconds = lib.mkOption {
      type = lib.types.int;
      default = 21600;
      description = "A pending Jellyseerr request younger than this pre-warms the chain so an approval never hands off to a dead Radarr; an older ignored pending request does not, and if it is finally approved the resulting failed request is retried once the chain comes up.";
    };

    keepChainAlwaysOn = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "When true, the supervisor keeps the whole download chain up on every tick and never idles it down, trading the on-demand savings for a chain that is always running so Sonarr and Radarr can catch newly aired episodes of monitored series the moment they release. Leave false for pure on-demand.";
    };

    bindAddressKey = lib.mkOption {
      type = lib.types.str;
      default = "ARR_BIND_ADDR";
      description = "The .env key the supervisor reads at runtime to learn the tailnet address the *arr web UIs listen on, so the tailscale IP stays out of the nix source and lives only in the build-generated .env.";
    };

    jellyseerrUrl = lib.mkOption {
      type = lib.types.str;
      default = "http://127.0.0.1:5055";
      description = "Loopback base URL of the always-on Jellyseerr the supervisor queries for actionable requests and drives retries against, using the API key read from its settings.json.";
    };

    radarrPort = lib.mkOption {
      type = lib.types.str;
      default = "7878";
      description = "Radarr web UI port the supervisor queries for the active download queue, combined with the bind address read from .env.";
    };

    sonarrPort = lib.mkOption {
      type = lib.types.str;
      default = "8989";
      description = "Sonarr web UI port the supervisor queries for the active download queue, combined with the bind address read from .env.";
    };
  };

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
