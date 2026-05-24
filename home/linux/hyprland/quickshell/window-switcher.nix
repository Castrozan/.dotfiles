{
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
  xdg.configFile."quickshell/switcher" = {
    source = ../../../../.config/quickshell/switcher;
    recursive = true;
  };

  systemd.user.services.quickshell-switcher = {
    Unit = {
      Description = "Quickshell window switcher with thumbnails";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
      X-Restart-Triggers = [ "${quickshellPackage}" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${quickshellPackage}/bin/quickshell -c switcher";
      Environment = [
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
