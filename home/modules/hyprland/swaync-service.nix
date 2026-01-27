{ pkgs, ... }:
{
  home.packages = [ pkgs.swaynotificationcenter ];

  systemd.user.services.swaync = {
    Unit = {
      Description = "Sway Notification Center";
      Documentation = "https://github.com/ErikReider/SwayNotificationCenter";
      PartOf = [ "graphical-session.target" ];
      After = [ "graphical-session.target" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${pkgs.swaynotificationcenter}/bin/swaync";
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
