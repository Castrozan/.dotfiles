{
  config,
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };

  quickshellPackage = nixglWrap.wrapWithNixGLIntel {
    package = pkgs.quickshell;
    binaries = [ "quickshell" ];
  };
in
{
  home.packages = [ quickshellPackage ];

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
      ExecStart = "${quickshellPackage}/bin/quickshell --path ${config.home.homeDirectory}/.dotfiles/.config/quickshell/bar";
      Environment = [
        "QML_IMPORT_PATH=${pkgs.qt6Packages.qt5compat}/lib/qt-6/qml"
        "QT_QPA_PLATFORM=wayland"
      ];
      Nice = -5;
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
