{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;
in
{
  options.openclaw.gatewayService.skipStaleCrons = {
    enable = lib.mkEnableOption "skip stale cron jobs on gateway start (missed while PC was off)";

    thresholdMinutes = lib.mkOption {
      type = lib.types.int;
      default = 30;
      description = "Skip cron jobs missed by more than this many minutes. Jobs missed within the threshold still catch up (e.g. quick gateway restarts).";
    };
  };

  config =
    let
      cfg = openclaw.gatewayService.skipStaleCrons;
      thresholdMs = cfg.thresholdMinutes * 60 * 1000;
    in
    lib.mkIf cfg.enable {
      openclaw.gatewayService.preStartScripts.skipStaleCrons = ''
        # Advance lastRunAtMs for cron jobs missed beyond threshold so
        # the gateway's runMissedJobs() catch-up logic skips them.
        JOBS_FILE="${homeDir}/.openclaw/cron/jobs.json"
        if [ -f "$JOBS_FILE" ]; then
          NOW_MS=$(( $(date +%s) * 1000 ))
          ${pkgs.jq}/bin/jq --argjson now "$NOW_MS" --argjson threshold ${toString thresholdMs} '
            .jobs |= map(
              if .enabled and .schedule.kind == "cron"
                and ((.state.lastRunAtMs // 0) < ($now - $threshold))
              then .state.nextRunAtMs = null | .state.lastRunAtMs = $now
              else . end
            )
          ' "$JOBS_FILE" > "$JOBS_FILE.tmp" && mv "$JOBS_FILE.tmp" "$JOBS_FILE"
        fi
      '';
    };
}
