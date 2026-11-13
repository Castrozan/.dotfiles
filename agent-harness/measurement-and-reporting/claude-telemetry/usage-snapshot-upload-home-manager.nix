{
  pkgs,
  lib,
  config,
  ...
}:
let
  ccusage = import ../../../machine-configuration/development/cost-monitoring/ccusage-package.nix {
    inherit pkgs;
  };

  ingestApiBaseUrl = "https://lucaszanoni.com/ingest";
  ingestProducerSecretPath = "${config.home.homeDirectory}/.secrets/ingest-producer-secret";
  ingestPublishIntervalSeconds = 300;
  ingestPublishTimeoutSeconds = 150;

  usageSnapshotSource = lib.fileset.toSource {
    root = ../usage-collection;
    fileset = lib.fileset.fileFilter (file: file.hasExt "py") ../usage-collection;
  };

  ingestionPublisherSource = lib.fileset.toSource {
    root = ../snapshot-ingestion;
    fileset = lib.fileset.fileFilter (file: file.hasExt "py") ../snapshot-ingestion;
  };

  usageSnapshotScripts = pkgs.runCommand "claude-usage-snapshot-scripts" { } ''
    mkdir -p "$out"
    cp ${usageSnapshotSource}/*.py "$out"/
    cp ${ingestionPublisherSource}/*.py "$out"/
  '';

  ingestPublishLauncher = pkgs.writeShellScript "claude-usage-ingest-publish" ''
    set -euo pipefail
    INGEST_PRODUCER_SECRET="$(cat "${ingestProducerSecretPath}")"
    export INGEST_PRODUCER_SECRET
    export PATH="${lib.makeBinPath [ ccusage ]}"
    exec "${pkgs.python312}/bin/python" \
      "${usageSnapshotScripts}/publish_current_usage_snapshot_to_ingest.py"
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
          StandardOutPath = "/tmp/claude-usage-ingest-publish.log";
          StandardErrorPath = "/tmp/claude-usage-ingest-publish.log";
        };
      };
    })
    (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
      systemd.user = {
        services = {
          claude-usage-ingest-publish = {
            Unit.Description = "Publish the anonymized Claude usage snapshot under its ingestion contract";
            Service = {
              Type = "oneshot";
              ExecStart = "${ingestPublishLauncher}";
              Environment = ingestPublishEnvironmentList;
              TimeoutStartSec = "${toString ingestPublishTimeoutSeconds}s";
            };
          };
        };
        timers = {
          claude-usage-ingest-publish = {
            Unit.Description = "Periodic contracted Claude usage publish to the ingestion api";
            Timer = {
              OnBootSec = "3min";
              OnUnitActiveSec = "${toString ingestPublishIntervalSeconds}s";
              Persistent = true;
            };
            Install.WantedBy = [ "timers.target" ];
          };
        };
      };
    })
  ];
}
