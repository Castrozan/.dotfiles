{ pkgs, ... }:
{
  xdg.configFile."quickshell/switcher" = {
    source = ../../../.config/quickshell/switcher;
    recursive = true;
  };

  systemd.user.services.quickshell-switcher = {
    Unit = {
      Description = "Quickshell window switcher with thumbnails";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "simple";
      ExecStart = "${pkgs.quickshell}/bin/quickshell -c switcher";
      Environment = [ "QT_QUICK_BACKEND=software" ];
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
