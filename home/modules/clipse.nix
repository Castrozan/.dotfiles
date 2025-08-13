{ pkgs, ... }:
{
  # Configure clipse as a systemd user service to run in the background
  systemd.user.services.clipse = {
    Unit = {
      Description = "Clipse clipboard manager";
      After = [ "graphical-session.target" ];
    };

    Service = {
      ExecStart = "${pkgs.clipse}/bin/clipse --listen-shell";
      Restart = "on-failure";
      RestartSec = "5s";
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };

  # Enable the service to start automatically
  systemd.user.startServices = "sd-switch";
}
