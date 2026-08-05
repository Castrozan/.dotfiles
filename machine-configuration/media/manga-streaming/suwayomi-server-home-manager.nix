{
  config,
  latest,
  ...
}:
let
  homeDir = config.home.homeDirectory;
in
{
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
    };

    Install = {
      WantedBy = [ ];
    };
  };

  systemd.user.startServices = "sd-switch";
}
