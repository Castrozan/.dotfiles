{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  inherit (config.home) homeDirectory username;
  homeDir = homeDirectory;
  nodejs = pkgs.nodejs_22;
  prefix = "$HOME/.local/share/openclaw-npm";

  nixSystemPaths = lib.concatStringsSep ":" [
    "${nodejs}/bin"
    "${pkgs.git}/bin"
    "/run/current-system/sw/bin"
    "/etc/profiles/per-user/${username}/bin"
    "${homeDir}/.nix-profile/bin"
    "/usr/bin"
    "/bin"
  ];

  secretsDirectory = "${homeDir}/.secrets";

  gatewayScript = pkgs.writeShellScript "openclaw-gateway" ''
    export PATH="${nodejs}/bin:''${PATH:+:$PATH}"
    export NPM_CONFIG_PREFIX="${prefix}"
    export NPM_CONFIG_REGISTRY="https://registry.npmjs.org/"

    if [ -f "${secretsDirectory}/gemini-api-key" ]; then
      GEMINI_API_KEY="$(cat "${secretsDirectory}/gemini-api-key")"
      export GEMINI_API_KEY
    fi

    if [ -f "${secretsDirectory}/openai-api-key" ]; then
      OPENAI_API_KEY="$(cat "${secretsDirectory}/openai-api-key")"
      export OPENAI_API_KEY
    fi

    if [ -f "${secretsDirectory}/nvidia-api-key" ]; then
      NVIDIA_API_KEY="$(cat "${secretsDirectory}/nvidia-api-key")"
      export NVIDIA_API_KEY
    fi

    OPENCLAW_BIN="${prefix}/bin/openclaw"
    if [ ! -x "$OPENCLAW_BIN" ]; then
      echo "OpenClaw not installed yet. Run 'openclaw --version' first to trigger auto-install."
      exit 1
    fi

    # Skip stale cron jobs missed while PC was off (>30 min threshold)
    JOBS_FILE="${homeDir}/.openclaw/cron/jobs.json"
    if [ -f "$JOBS_FILE" ]; then
      NOW_MS=$(( $(date +%s) * 1000 ))
      ${pkgs.jq}/bin/jq --argjson now "$NOW_MS" --argjson threshold 1800000 '
        .jobs |= map(
          if .enabled and .schedule.kind == "cron"
            and ((.state.lastRunAtMs // 0) < ($now - $threshold))
          then .state.nextRunAtMs = null | .state.lastRunAtMs = $now
          else . end
        )
      ' "$JOBS_FILE" > "$JOBS_FILE.tmp" && mv "$JOBS_FILE.tmp" "$JOBS_FILE"
    fi

    exec "$OPENCLAW_BIN" gateway --port ${toString openclaw.gatewayPort}
  '';
in
{
  options.openclaw.gatewayService.enable = lib.mkEnableOption "OpenClaw gateway systemd user service";

  config = lib.mkIf openclaw.gatewayService.enable {
    systemd.user.services.openclaw-gateway = {
      Unit = {
        Description = "OpenClaw Gateway (port ${toString openclaw.gatewayPort})";
        After = [ "network.target" ];
      };

      Service = {
        Type = "simple";
        ExecStart = "${gatewayScript}";
        Restart = "always";
        RestartSec = "2s";
        TimeoutStopSec = "10s";
        KillMode = "control-group";
        CPUQuota = "150%";
        MemoryMax = "2G";
        OOMScoreAdjust = -500;
        Environment = [
          "PATH=${nixSystemPaths}"
          "NODE_ENV=production"
          "OPENCLAW_NIX_MODE=1"
        ];
      };

      Install = {
        WantedBy = [ "default.target" ];
      };
    };
  };
}
