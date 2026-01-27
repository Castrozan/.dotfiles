{ pkgs, ... }:
{
  systemd.user.services.swayosd = {
    Unit = {
      Description = "SwayOSD notification daemon";
      Documentation = "https://github.com/ErikReider/SwayOSD";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "simple";
      ExecStart = "${pkgs.swayosd}/bin/swayosd-server";
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
