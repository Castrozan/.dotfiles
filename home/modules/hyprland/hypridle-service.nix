{ pkgs, ... }:
{
  systemd.user.services.hypridle = {
    Unit = {
      Description = "Hyprland idle daemon";
      Documentation = "https://github.com/hyprwm/hypridle";
      PartOf = [ "graphical-session.target" ];
      After = [ "graphical-session.target" ];
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
