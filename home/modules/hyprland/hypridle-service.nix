{ pkgs, ... }:
{
  systemd.user.services.hypridle = {
    Unit = {
      Description = "Hyprland idle daemon";
      Documentation = "https://github.com/hyprwm/hypridle";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "simple";
      ExecStart = "${pkgs.hypridle}/bin/hypridle";
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
