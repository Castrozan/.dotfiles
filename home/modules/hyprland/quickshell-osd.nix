{ pkgs, ... }:
{
  home.packages = [ pkgs.quickshell ];

  xdg.configFile."quickshell/osd" = {
    source = ../../../.config/quickshell/osd;
    recursive = true;
  };

  systemd.user.services.quickshell-osd = {
    Unit = {
      Description = "Quickshell OSD overlay for volume and brightness";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "simple";
      ExecStart = "${pkgs.quickshell}/bin/quickshell -c osd";
      Environment = [ "QT_QUICK_BACKEND=software" ];
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
