{ pkgs, ... }:
{
  xdg.configFile."quickshell/bar" = {
    source = ../../../.config/quickshell/bar;
    recursive = true;
  };

  systemd.user.services.quickshell-bar = {
    Unit = {
      Description = "Quickshell vertical bar replacing waybar";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "simple";
      ExecStart = "${pkgs.quickshell}/bin/quickshell -c bar";
      Environment = [ "QT_QUICK_BACKEND=software" ];
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
