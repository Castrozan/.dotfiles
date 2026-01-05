{
  config,
  latest,
  ...
}:
let
  homeDir = config.home.homeDirectory;
in
{
  # Configure suwayomi-server as a systemd user service to run in the background
  systemd.user.services.suwayomi-server = {
    Unit = {
      Description = "Suwayomi-Server - Manga server";
      After = [ "network.target" ];
    };

    Service = {
      ExecStart = "${latest.suwayomi-server}/bin/tachidesk-server";
      Restart = "on-failure";
      RestartSec = "5s";
      WorkingDirectory = homeDir;
      Environment = [
        "HOME=${homeDir}"
        "TACHIDESK_DATA_DIR=${homeDir}/.local/share/Tachidesk"
      ];
      # Data directory set explicitly to avoid logback config issues
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };

  # Enable the service to start automatically
  systemd.user.startServices = "sd-switch";
}
