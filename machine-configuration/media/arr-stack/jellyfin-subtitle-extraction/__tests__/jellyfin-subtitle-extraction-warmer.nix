{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  evalWarmer =
    settings:
    (lib.evalModules {
      specialArgs = { inherit pkgs; };
      modules = [
        ../jellyfin-subtitle-extraction-warmer-nixos.nix
        {
          options.systemd = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.jellyfinSubtitleExtractionWarmer = settings;
        }
      ];
    }).config;

  baseSettings = {
    enable = true;
    jellyfinApiKeySecretFile = "/run/agenix/jellyfin-admin-api-key";
    jellyfinDataDirectory = "/home/zanoni/arr-stack/config/jellyfin/data/data";
  };

  warmerDisabled = evalWarmer (baseSettings // { enable = false; });
  warmerEnabled = evalWarmer baseSettings;
  enabledService = warmerEnabled.systemd.services.jellyfin-subtitle-extraction-warmer;
  enabledTimer = warmerEnabled.systemd.timers.jellyfin-subtitle-extraction-warmer;
  enabledEnvironment = enabledService.environment;
in
{
  chise-jellyfin-subtitle-warmer-disabled-defines-no-unit =
    mkEvalCheck "chise-jellyfin-subtitle-warmer-disabled-defines-no-unit"
      (
        !(warmerDisabled.systemd.services or { } ? jellyfin-subtitle-extraction-warmer)
        && !(warmerDisabled.systemd.timers or { } ? jellyfin-subtitle-extraction-warmer)
      )
      "a host that does not opt in must get neither the service nor the timer, so an unopted host never reads its media disk to pre-extract subtitles";

  chise-jellyfin-subtitle-warmer-runs-only-from-its-timer =
    mkEvalCheck "chise-jellyfin-subtitle-warmer-runs-only-from-its-timer"
      (
        enabledService.serviceConfig.Type == "oneshot"
        && lib.hasInfix "jellyfin_subtitle_extraction_warmer" enabledService.serviceConfig.ExecStart
        && !(builtins.elem "multi-user.target" (enabledService.wantedBy or [ ]))
        && builtins.elem "timers.target" enabledTimer.wantedBy
        && enabledTimer.timerConfig.OnUnitInactiveSec == "30min"
        && !(enabledTimer.timerConfig ? OnUnitActiveSec)
        && enabledTimer.timerConfig.Persistent
      )
      "the sweep must be a oneshot pulled in only by its timer, never by multi-user.target, so a rebuild never starts a long disk-bound extraction run in the middle of someone watching, and a machine that was off catches up on its next boot; the interval runs from the end of the previous sweep because a sweep that waits out a binge before extracting has no bounded length to measure from its start";

  chise-jellyfin-subtitle-warmer-reads-agenix-key-and-cache-directory =
    mkEvalCheck "chise-jellyfin-subtitle-warmer-reads-agenix-key-and-cache-directory"
      (
        lib.hasInfix "agenix" enabledEnvironment.JELLYFIN_SUBTITLE_EXTRACTION_WARMER_API_KEY_FILE
        && lib.hasSuffix "data/data" enabledEnvironment.JELLYFIN_SUBTITLE_EXTRACTION_WARMER_DATA_DIRECTORY
        && lib.hasInfix "127.0.0.1" enabledEnvironment.JELLYFIN_SUBTITLE_EXTRACTION_WARMER_BASE_URL
      )
      "the warmer must authenticate from an agenix file path over loopback and be pointed at Jellyfin's doubled data directory, so no secret is committed, warming never depends on the tailnet, and the cache probe looks where the linuxserver image actually writes extracted subtitles";

  chise-jellyfin-subtitle-warmer-bounds-one-sweep =
    mkEvalCheck "chise-jellyfin-subtitle-warmer-bounds-one-sweep"
      (
        enabledEnvironment.JELLYFIN_SUBTITLE_EXTRACTION_WARMER_ITEM_BUDGET == "20"
        && enabledEnvironment.JELLYFIN_SUBTITLE_EXTRACTION_WARMER_PAUSE_SECONDS == "5"
        && enabledService.serviceConfig.RuntimeMaxSec > 0
      )
      "one sweep must carry a per-item budget, a pause between items and a hard runtime ceiling, so a freshly filled library, a cache-layout change in a future Jellyfin, or a wait for a gap that never comes cannot pin the media disk or leave a unit running forever";

  chise-jellyfin-subtitle-warmer-waits-for-a-gap-between-playbacks =
    mkEvalCheck "chise-jellyfin-subtitle-warmer-waits-for-a-gap-between-playbacks"
      (
        enabledEnvironment.JELLYFIN_SUBTITLE_EXTRACTION_WARMER_QUIET_POLL_SECONDS == "30"
        && enabledEnvironment.JELLYFIN_SUBTITLE_EXTRACTION_WARMER_QUIET_WAIT_SECONDS == "1200"
        &&
          lib.toInt enabledEnvironment.JELLYFIN_SUBTITLE_EXTRACTION_WARMER_QUIET_WAIT_SECONDS
          > lib.toInt enabledEnvironment.JELLYFIN_SUBTITLE_EXTRACTION_WARMER_QUIET_POLL_SECONDS
      )
      "a sweep must wait for a gap rather than give up the moment it finds playback, because a long binge is exactly when newly imported episodes need extracting and a timer that only fires into an already-idle server would never reach them";
}
