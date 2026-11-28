{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:
let
  usageCollector = inputs.usage-reporting.packages.${pkgs.stdenv.hostPlatform.system}.default;

  litellmModelPrices = pkgs.fetchurl {
    url = "https://raw.githubusercontent.com/BerriAI/litellm/36d3fa37f74b9b96f05487a82eee7a94143e4e05/model_prices_and_context_window.json";
    hash = "sha256-i4UujZlIBf91KVRE7W6srhaEtMP0rfwhyJ8mW3i/Too=";
  };

  ingestApiBaseUrl = "https://lucaszanoni.com/ingest";
  ingestProducerSecretPath = "${config.home.homeDirectory}/.secrets/ingest-producer-secret";
  ingestPublishIntervalSeconds = 300;
  ingestPublishTimeoutSeconds = 150;

  ingestPublishLauncher = pkgs.writeShellScript "claude-usage-ingest-publish" ''
    set -euo pipefail
    INGEST_PRODUCER_SECRET="$(cat "${ingestProducerSecretPath}")"
    export INGEST_PRODUCER_SECRET
    exec "${lib.getExe usageCollector}" publish --pricing-file "${litellmModelPrices}"
  '';

  ingestPublishEnvironment = {
    INGEST_BASE_URL = ingestApiBaseUrl;
  };

  ingestPublishEnvironmentList = lib.mapAttrsToList (
    name: value: "${name}=${value}"
  ) ingestPublishEnvironment;
in
{
  config = lib.mkMerge [
    (lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
      launchd.agents.claude-usage-ingest-publish = {
        enable = true;
        config = {
          Label = "com.dotfiles.claude-usage-ingest-publish";
          ProgramArguments = [ "${ingestPublishLauncher}" ];
          EnvironmentVariables = ingestPublishEnvironment;
          RunAtLoad = true;
          StartInterval = ingestPublishIntervalSeconds;
          ProcessType = "Background";
          LowPriorityIO = true;
          Nice = 19;
          StandardOutPath = "/tmp/claude-usage-ingest-publish.log";
          StandardErrorPath = "/tmp/claude-usage-ingest-publish.log";
        };
      };
    })
    (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
      systemd.user = {
        services.claude-usage-ingest-publish = {
          Unit.Description = "Publish the anonymized Claude usage snapshot under its ingestion contract";
          Service = {
            Type = "oneshot";
            ExecStart = "${ingestPublishLauncher}";
            Environment = ingestPublishEnvironmentList;
            TimeoutStartSec = "${toString ingestPublishTimeoutSeconds}s";
            Nice = 19;
            IOSchedulingClass = "idle";
            MemoryHigh = "512M";
          };
        };
        timers.claude-usage-ingest-publish = {
          Unit.Description = "Periodic contracted Claude usage publish to the ingestion api";
          Timer = {
            OnBootSec = "3min";
            OnUnitActiveSec = "${toString ingestPublishIntervalSeconds}s";
            Persistent = true;
          };
          Install.WantedBy = [ "timers.target" ];
        };
      };
    })
  ];
}
