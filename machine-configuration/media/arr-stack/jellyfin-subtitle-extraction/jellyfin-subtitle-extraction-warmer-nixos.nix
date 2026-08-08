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
      description = "How long after a finished sweep the next one starts; short enough that a freshly imported episode is extracted well before anyone opens it, and every sweep is a no-op once the library is fully extracted.";
    };

    itemBudgetPerSweep = lib.mkOption {
      type = lib.types.int;
      default = 20;
      description = "Maximum number of videos one sweep extracts. Each extraction reads a whole file off the media disk, so a bounded sweep keeps a freshly filled library from pinning the disk for hours and caps the damage if a future Jellyfin changes its cache layout and every probe starts reporting work to do.";
    };

    pauseSecondsBetweenItems = lib.mkOption {
      type = lib.types.int;
      default = 5;
      description = "Idle gap left between videos so the media disk and the Jellyfin container are never saturated back to back by the sweep.";
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
        JELLYFIN_SUBTITLE_EXTRACTION_WARMER_PAUSE_SECONDS = toString warmerConfig.pauseSecondsBetweenItems;
      };
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${pkgs.python3}/bin/python3 ${warmerPackageDirectory}";
      };
    };

    systemd.timers.jellyfin-subtitle-extraction-warmer = {
      description = "Sweep the Jellyfin library for embedded subtitle tracks that are not extracted yet";
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnBootSec = "10min";
        OnUnitActiveSec = warmerConfig.sweepInterval;
        Persistent = true;
      };
    };
  };
}
