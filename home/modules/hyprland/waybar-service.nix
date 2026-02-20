{ pkgs, config, ... }:
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
      Environment = "PATH=${config.home.profileDirectory}/bin:/run/current-system/sw/bin:/usr/bin:/bin";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
