{ config, pkgs, ... }:
{
  home.packages = [ pkgs.quickshell ];

  xdg.configFile."quickshell/bar" = {
    source = ../../../../.config/quickshell/bar;
    recursive = true;
  };

  systemd.user.services.quickshell-bar = {
    Unit = {
      Description = "Quickshell vertical bar";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "simple";
      ExecStart = "${pkgs.quickshell}/bin/quickshell --path ${config.home.homeDirectory}/.dotfiles/.config/quickshell/bar";
      Environment = [
        "QML_IMPORT_PATH=${pkgs.qt6Packages.qt5compat}/lib/qt-6/qml"
      ];
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
