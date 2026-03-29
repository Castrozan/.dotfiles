{ pkgs, ... }:
{
  systemd.user.services.hyprpaper = {
    Unit = {
      Description = "Hyprpaper wallpaper daemon";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "simple";
      ExecStart = "${pkgs.hyprpaper}/bin/hyprpaper";
      Restart = "always";
      RestartSec = "2s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
