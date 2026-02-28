{ pkgs, ... }:
{
  xdg.configFile."quickshell/dashboard" = {
    source = ../../../.config/quickshell/dashboard;
    recursive = true;
  };

  systemd.user.services.quickshell-dashboard = {
    Unit = {
      Description = "Quickshell media dashboard overlay";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "simple";
      ExecStart = "${pkgs.quickshell}/bin/quickshell -c dashboard";
      Environment = [ "QT_QUICK_BACKEND=software" ];
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
