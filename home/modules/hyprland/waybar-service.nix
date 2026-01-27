{ pkgs, ... }:
{
  systemd.user.services.waybar = {
    Unit = {
      Description = "Waybar status bar";
      Documentation = "https://github.com/Alexays/Waybar";
      PartOf = [ "graphical-session.target" ];
      After = [ "graphical-session.target" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${pkgs.waybar}/bin/waybar";
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
