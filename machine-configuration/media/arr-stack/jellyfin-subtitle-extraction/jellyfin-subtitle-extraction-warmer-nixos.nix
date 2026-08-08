{
  config,
  lib,
  pkgs,
  ...
}:
let
  warmerConfig = config.custom.jellyfinSubtitleExtractionWarmer;
  warmerPackageDirectory = ./scripts/jellyfin_subtitle_extraction_warmer;
in
{
  options.custom.jellyfinSubtitleExtractionWarmer = {
    enable = lib.mkEnableOption "a timer that extracts every embedded text subtitle track ahead of playback, so the player never stalls on 'Fetching additional data'. Jellyfin extracts embedded subtitles with ffmpeg on the first request for them, which demuxes the whole file and costs twenty to thirty seconds off a spinning disk while the client sits on a spinner; extraction results are cached forever under the Jellyfin data directory, so doing it on a timer while nobody is watching moves that cost off the viewer entirely";

    jellyfinBaseUrl = lib.mkOption {
      type = lib.types.str;
      default = "http://127.0.0.1:8096";
      description = "Base URL the warmer talks to Jellyfin on; the loopback publish of the jellyfin container, so warming never depends on the tailnet being up.";
    };

    jellyfinApiKeySecretFile = lib.mkOption {
      type = lib.types.str;
      description = "Path to the agenix-decrypted Jellyfin admin API key the warmer authenticates with; the same key the other Jellyfin reconcilers read.";
    };

    jellyfinDataDirectory = lib.mkOption {
      type = lib.types.str;
      description = "Host path of Jellyfin's data directory, holding the subtitles cache the warmer probes to tell an already-extracted track from a pending one. The linuxserver image points Jellyfin's data path at /config/data, so on the host this is the doubled data/data path under the bind-mounted config root.";
    };

    sweepInterval = lib.mkOption {
      type = lib.types.str;
      default = "30min";
      description = "How long after a finished sweep the next one starts. It is measured from the end rather than the start of the previous run, because a sweep waits for a gap between playbacks and then extracts, so its own length is unbounded enough that a start-relative interval would queue runs behind each other.";
    };

    itemBudgetPerSweep = lib.mkOption {
      type = lib.types.int;
      default = 20;
      description = "Maximum number of videos one sweep extracts. Each extraction reads a whole file off the media disk, so a bounded sweep keeps a freshly filled library from pinning the disk for hours and caps the damage if a future Jellyfin changes its cache layout and every probe starts reporting work to do.";
    };

    busyItemBudgetPerSweep = lib.mkOption {
      type = lib.types.int;
      default = 3;
      description = "How many videos a sweep extracts when it never found a gap and gives up waiting. A binge is exactly when a stall is most likely and least welcome, so the sweep extracts a handful of titles alongside the stream rather than nothing at all; it stays far below the quiet-server budget because those reads compete with playback on the same disk.";
    };

    pauseSecondsBetweenItems = lib.mkOption {
      type = lib.types.int;
      default = 5;
      description = "Idle gap left between videos so the media disk and the Jellyfin container are never saturated back to back by the sweep.";
    };

    quietPollSeconds = lib.mkOption {
      type = lib.types.int;
      default = 30;
      description = "How often a started sweep re-asks Jellyfin whether anybody is watching while it waits for a gap. Two quiet answers in a row are required before extraction begins, so the few seconds between one episode ending and the next one autoplaying never look like an idle server.";
    };

    quietWaitSeconds = lib.mkOption {
      type = lib.types.int;
      default = 1200;
      description = "How long a sweep waits for that gap before giving up until the next timer fire. Without the wait a long binge would never surface an idle moment at the instant the timer happens to fire, and freshly imported episodes would still stall on their first play.";
    };
  };

  config = lib.mkIf warmerConfig.enable {
    systemd.services.jellyfin-subtitle-extraction-warmer = {
      description = "Extract embedded subtitle tracks ahead of playback so Jellyfin never stalls fetching them";
      after = [
        "docker.service"
        "network-online.target"
      ];
      wants = [ "network-online.target" ];
      environment = {
        JELLYFIN_SUBTITLE_EXTRACTION_WARMER_BASE_URL = warmerConfig.jellyfinBaseUrl;
        JELLYFIN_SUBTITLE_EXTRACTION_WARMER_API_KEY_FILE = warmerConfig.jellyfinApiKeySecretFile;
        JELLYFIN_SUBTITLE_EXTRACTION_WARMER_DATA_DIRECTORY = warmerConfig.jellyfinDataDirectory;
        JELLYFIN_SUBTITLE_EXTRACTION_WARMER_ITEM_BUDGET = toString warmerConfig.itemBudgetPerSweep;
        JELLYFIN_SUBTITLE_EXTRACTION_WARMER_BUSY_ITEM_BUDGET = toString warmerConfig.busyItemBudgetPerSweep;
        JELLYFIN_SUBTITLE_EXTRACTION_WARMER_PAUSE_SECONDS = toString warmerConfig.pauseSecondsBetweenItems;
        JELLYFIN_SUBTITLE_EXTRACTION_WARMER_QUIET_POLL_SECONDS = toString warmerConfig.quietPollSeconds;
        JELLYFIN_SUBTITLE_EXTRACTION_WARMER_QUIET_WAIT_SECONDS = toString warmerConfig.quietWaitSeconds;
      };
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${pkgs.python3}/bin/python3 ${warmerPackageDirectory}";
        TimeoutStartSec = 7200;
      };
    };

    systemd.timers.jellyfin-subtitle-extraction-warmer = {
      description = "Sweep the Jellyfin library for embedded subtitle tracks that are not extracted yet";
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnBootSec = "10min";
        OnUnitInactiveSec = warmerConfig.sweepInterval;
        Persistent = true;
      };
    };
  };
}
