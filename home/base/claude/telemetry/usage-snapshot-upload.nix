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
  uploadIntervalSeconds = 300;

  uploaderPythonEnvironment = pkgs.python312.withPackages (pythonPackages: [
    pythonPackages.google-cloud-storage
  ]);

  usageSnapshotSource = lib.fileset.toSource {
    root = ../../../../agents/usage;
    fileset = lib.fileset.fileFilter (file: file.hasExt "py") ../../../../agents/usage;
  };

  usageSnapshotScripts = pkgs.runCommand "claude-usage-snapshot-scripts" { } ''
    mkdir -p "$out"
    cp ${usageSnapshotSource}/*.py "$out"/
  '';

  uploadProgramArguments = [
    "${uploaderPythonEnvironment}/bin/python"
    "${usageSnapshotScripts}/upload_usage_snapshot_to_gcs.py"
  ];

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
    })
    (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
      systemd.user.services.claude-usage-snapshot-upload = {
        Unit.Description = "Upload anonymized Claude usage snapshot to GCS";
        Service = {
          Type = "oneshot";
          ExecStart = lib.concatStringsSep " " uploadProgramArguments;
          Environment = uploadEnvironmentList;
        };
      };
      systemd.user.timers.claude-usage-snapshot-upload = {
        Unit.Description = "Periodic anonymized Claude usage snapshot upload to GCS";
        Timer = {
          OnBootSec = "2min";
          OnUnitActiveSec = "${toString uploadIntervalSeconds}s";
          Persistent = true;
        };
        Install.WantedBy = [ "timers.target" ];
      };
    })
  ];
}
