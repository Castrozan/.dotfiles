{
  pkgs,
  lib,
  ...
}:
let
  driftCheckIntervalSeconds = 300;

  chromeGlobalLauncher = import ./chrome-global-launcher.nix { inherit pkgs; };
  chromeGlobalLauncherBinary = "${chromeGlobalLauncher.chromeGlobalLauncherPackage}/bin/summon-chrome-global";

  versionDriftRestarterPythonEnvironment = pkgs.python312.withPackages (pythonPackages: [
    pythonPackages.psutil
  ]);

  versionDriftRestarterSource = lib.fileset.toSource {
    root = ./scripts/chrome_global_version_drift_restarter;
    fileset = lib.fileset.fileFilter (
      file: file.hasExt "py"
    ) ./scripts/chrome_global_version_drift_restarter;
  };

  versionDriftRestarterEntrypoint = "${versionDriftRestarterSource}/restart_chrome_global_on_version_drift.py";

  versionDriftRestarterProgramArguments = [
    "${versionDriftRestarterPythonEnvironment}/bin/python"
    versionDriftRestarterEntrypoint
    "--launcher-binary"
    chromeGlobalLauncherBinary
  ];

  versionDriftRestarterLogFilePath = "/tmp/chrome-global-version-drift-restarter.log";
in
{
  launchd.agents.chrome-global-version-drift-restarter = {
    enable = true;
    config = {
      Label = "com.dotfiles.chrome-global-version-drift-restarter";
      ProgramArguments = versionDriftRestarterProgramArguments;
      RunAtLoad = true;
      StartInterval = driftCheckIntervalSeconds;
      StandardOutPath = versionDriftRestarterLogFilePath;
      StandardErrorPath = versionDriftRestarterLogFilePath;
    };
  };
}
