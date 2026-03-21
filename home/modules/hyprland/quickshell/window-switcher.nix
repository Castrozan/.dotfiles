{
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
  xdg.configFile."quickshell/switcher" = {
    source = ../../../../.config/quickshell/switcher;
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
      ExecStart = "${quickshellPackage}/bin/quickshell -c switcher";
      Environment = [ "QT_QPA_PLATFORM=wayland" ];
      Nice = -5;
      Restart = "always";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
