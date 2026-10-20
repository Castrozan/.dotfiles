{
  config,
  lib,
  pkgs,
  ...
}:
let
  maximumAgeHours = 24;
  cleanupIntervalSeconds = 3600;
  cleanupLogPath = "/tmp/temporary-directory-cleanup.log";

  agenixTopLevelNames = map builtins.baseNameOf [
    config.age.secretsDir
    config.age.secretsMountPoint
  ];
in
{
  launchd.agents.temporary-directory-cleanup = {
    enable = true;
    config = {
      Label = "com.dotfiles.temporary-directory-cleanup";
      ProgramArguments = [
        "${pkgs.python312}/bin/python3"
        "${./scripts/temporary_directory_cleanup.py}"
        "--maximum-age-hours"
        (toString maximumAgeHours)
      ]
      ++ lib.concatMap (name: [
        "--protect"
        name
      ]) agenixTopLevelNames;
      RunAtLoad = true;
      StartInterval = cleanupIntervalSeconds;
      ProcessType = "Background";
      LowPriorityIO = true;
      Nice = 10;
      StandardOutPath = cleanupLogPath;
      StandardErrorPath = cleanupLogPath;
    };
  };
}
