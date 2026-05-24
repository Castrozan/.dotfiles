{
  config,
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };

  upstreamQuickshellPackage = inputs.quickshell.packages.${pkgs.system}.quickshell;

  quickshellPackage = nixglWrap.wrapWithNixGLIntel {
    package = upstreamQuickshellPackage;
    binaries = [ "quickshell" ];
  };
in
{
  home.packages = [
    quickshellPackage
    pkgs.cava
  ];

  xdg.configFile."quickshell/bar" = {
    source = ../../../../.config/quickshell/bar;
    recursive = true;
  };

  systemd.user.services.quickshell-bar = {
    Unit = {
      Description = "Quickshell vertical bar";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
      X-Restart-Triggers = [ "${quickshellPackage}" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${quickshellPackage}/bin/quickshell --path ${config.home.homeDirectory}/.dotfiles/.config/quickshell/bar";
      Environment = [
        "QML_IMPORT_PATH=${pkgs.qt6Packages.qt5compat}/lib/qt-6/qml"
        "QT_QPA_PLATFORM=wayland"
        "QS_DROP_EXPENSIVE_FONTS=1"
      ];
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
