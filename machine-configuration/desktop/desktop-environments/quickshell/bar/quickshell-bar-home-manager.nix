{
  config,
  lib,
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../../../../repository/nix-library/nixgl-wrap.nix {
    inherit pkgs inputs isNixOS;
  };

  quickshellPackage = nixglWrap.wrapWithNixGLIntel {
    package = pkgs.quickshell;
    binaries = [ "quickshell" ];
  };

  barIsActive = config.custom.desktopShell.active == "quickshell-bar";
in
{
  home.packages = [ quickshellPackage ] ++ lib.optional barIsActive pkgs.cava;

  custom.desktopShell = lib.mkIf barIsActive {
    hyprlandBindings = ''
      bindd = SUPER, J, Toggle left bar, exec, qs -c bar ipc --any-display call -- bar toggle
      bindd = SUPER, M, Media dashboard, exec, qs -c bar ipc --any-display call dashboard toggle
      # ipc --any-display is required on upstream-master quickshell: the service registers display as "wayland,wayland-1"
      # while the Hyprland exec sees only "wayland-1", so the default display filter rejects the match.
      bindd = SUPER, Q, Launcher, exec, qs -c bar ipc --any-display call launcher toggle
      bindd = SUPER, A, Notifications, exec, qs -c bar ipc --any-display call sidebar toggle
    '';
    sessionServices = [
      "quickshell-bar.service"
      "mako.service"
    ];
  };

  xdg.configFile."quickshell/bar" = lib.mkIf barIsActive {
    source = ./program-configuration;
    recursive = true;
  };

  systemd.user.services.quickshell-bar = lib.mkIf barIsActive {
    Unit = {
      Description = "Quickshell vertical bar";
      After = [ "graphical-session.target" ];
      PartOf = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
      X-Restart-Triggers = [ "${quickshellPackage}" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${quickshellPackage}/bin/quickshell -c bar";
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
