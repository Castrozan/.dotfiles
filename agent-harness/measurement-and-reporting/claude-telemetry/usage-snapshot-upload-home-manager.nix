{
  pkgs,
  lib,
  config,
  ...
}:
let
  usageSnapshotBucket = "zg-url-shortener-2026-dotfiles-usage-snapshots";
  usageSnapshotObjectPrefix = "snapshots/";
  uploaderCredentialsPath = "${config.home.homeDirectory}/.secrets/gcp-usage-uploader-key";
  ingestApiBaseUrl = "https://lucaszanoni.com/ingest";
  ingestProducerSecretPath = "${config.home.homeDirectory}/.secrets/ingest-producer-secret";
  uploadIntervalSeconds = 300;

  uploaderPythonEnvironment = pkgs.python312.withPackages (pythonPackages: [
    pythonPackages.google-cloud-storage
  ]);

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

  uploadProgramArguments = [
    "${uploaderPythonEnvironment}/bin/python"
    "${usageSnapshotScripts}/upload_usage_snapshot_to_gcs.py"
  ];

  ingestPublishLauncher = pkgs.writeShellScript "claude-usage-ingest-publish" ''
    set -euo pipefail
    INGEST_PRODUCER_SECRET="$(cat "${ingestProducerSecretPath}")"
    export INGEST_PRODUCER_SECRET
    exec "${uploaderPythonEnvironment}/bin/python" \
      "${usageSnapshotScripts}/publish_current_usage_snapshot_to_ingest.py"
  '';

  ingestPublishEnvironment = {
    INGEST_BASE_URL = ingestApiBaseUrl;
  };

  ingestPublishEnvironmentList = lib.mapAttrsToList (
    name: value: "${name}=${value}"
  ) ingestPublishEnvironment;

  uploadEnvironment = {
    USAGE_SNAPSHOT_BUCKET = usageSnapshotBucket;
    USAGE_SNAPSHOT_OBJECT_PREFIX = usageSnapshotObjectPrefix;
    GOOGLE_APPLICATION_CREDENTIALS = uploaderCredentialsPath;
  };

  uploadEnvironmentList = lib.mapAttrsToList (name: value: "${name}=${value}") uploadEnvironment;
in
{
  config = lib.mkMerge [
    (lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
      launchd.agents.claude-usage-snapshot-upload = {
        enable = true;
        config = {
          Label = "com.dotfiles.claude-usage-snapshot-upload";
          ProgramArguments = uploadProgramArguments;
          EnvironmentVariables = uploadEnvironment;
          RunAtLoad = true;
          StartInterval = uploadIntervalSeconds;
          StandardOutPath = "/tmp/claude-usage-snapshot-upload.log";
          StandardErrorPath = "/tmp/claude-usage-snapshot-upload.log";
        };
      };
      launchd.agents.claude-usage-ingest-publish = {
        enable = true;
        config = {
          Label = "com.dotfiles.claude-usage-ingest-publish";
          ProgramArguments = [ "${ingestPublishLauncher}" ];
          EnvironmentVariables = ingestPublishEnvironment;
          RunAtLoad = true;
          StartInterval = uploadIntervalSeconds;
          StandardOutPath = "/tmp/claude-usage-ingest-publish.log";
          StandardErrorPath = "/tmp/claude-usage-ingest-publish.log";
        };
      };
    })
    (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
      systemd.user = {
        services = {
          claude-usage-snapshot-upload = {
            Unit.Description = "Upload anonymized Claude usage snapshot to GCS";
            Service = {
              Type = "oneshot";
              ExecStart = lib.concatStringsSep " " uploadProgramArguments;
              Environment = uploadEnvironmentList;
            };
          };
          claude-usage-ingest-publish = {
            Unit.Description = "Publish the anonymized Claude usage snapshot under its ingestion contract";
            Service = {
              Type = "oneshot";
              ExecStart = "${ingestPublishLauncher}";
              Environment = ingestPublishEnvironmentList;
            };
          };
        };
        timers = {
          claude-usage-snapshot-upload = {
            Unit.Description = "Periodic anonymized Claude usage snapshot upload to GCS";
            Timer = {
              OnBootSec = "2min";
              OnUnitActiveSec = "${toString uploadIntervalSeconds}s";
              Persistent = true;
            };
            Install.WantedBy = [ "timers.target" ];
          };
          claude-usage-ingest-publish = {
            Unit.Description = "Periodic contracted Claude usage publish to the ingestion api";
            Timer = {
              OnBootSec = "3min";
              OnUnitActiveSec = "${toString uploadIntervalSeconds}s";
              Persistent = true;
            };
            Install.WantedBy = [ "timers.target" ];
          };
        };
      };
    })
  ];
}
