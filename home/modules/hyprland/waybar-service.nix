{ pkgs, ... }:
{
  systemd.user.services.waybar = {
    Unit = {
      Description = "Waybar status bar";
      Documentation = "https://github.com/Alexays/Waybar";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
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
