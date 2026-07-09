{ lib, ... }:
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

    diskGuard = {
      warningFreeGigabytes = lib.mkOption {
        type = lib.types.int;
        default = 30;
        description = "When free space on the guarded filesystem drops below this, the supervisor emails a warning once so the disk is topped up before it becomes critical.";
      };

      criticalFreeGigabytes = lib.mkOption {
        type = lib.types.int;
        default = 15;
        description = "When free space drops below this the supervisor stops the download client mid-fill and holds it out of the keep-chain-always-on restart, so a large grab can never fill the shared root partition to zero and take the whole host down; the client resumes automatically once space recovers.";
      };

      fillService = lib.mkOption {
        type = lib.types.str;
        default = "qbittorrent";
        description = "The compose service that writes downloads to disk and is stopped when free space is critical; it must be one of the on-demand services so the disk guard can hold it down.";
      };

      criticalReminderSeconds = lib.mkOption {
        type = lib.types.int;
        default = 21600;
        description = "How often a still-critical disk re-sends its alert, so a persistent low-disk condition keeps nagging without emailing on every poll.";
      };

      path = lib.mkOption {
        type = lib.types.str;
        default = "";
        description = "Absolute path whose filesystem free space is guarded; empty means the stack home directory, which on a single-partition host is the same filesystem downloads, config and the OS all share.";
      };

      alertSmtpHost = lib.mkOption {
        type = lib.types.str;
        default = "smtp.gmail.com";
        description = "SMTP submission host for disk alerts; defaults to Gmail so it can reuse the same app-password secret as the Jellyseerr email agent.";
      };

      alertSmtpPort = lib.mkOption {
        type = lib.types.int;
        default = 587;
        description = "SMTP submission port for disk alerts; STARTTLS is always used.";
      };

      alertSmtpUsername = lib.mkOption {
        type = lib.types.str;
        default = "";
        description = "SMTP auth username for disk alerts; empty disables the email so the guard still stops the fill service and logs, just without mailing.";
      };

      alertEmailSender = lib.mkOption {
        type = lib.types.str;
        default = "";
        description = "From address on disk alert mail.";
      };

      alertEmailRecipient = lib.mkOption {
        type = lib.types.str;
        default = "";
        description = "Recipient of disk alert mail.";
      };

      alertAppPasswordSecretFile = lib.mkOption {
        type = lib.types.str;
        default = "";
        description = "Path to the agenix-decrypted SMTP app password the root supervisor reads to send disk alerts; empty disables the email. Can point at the same secret the Jellyseerr email agent uses.";
      };
    };
  };
}
