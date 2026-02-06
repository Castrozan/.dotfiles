{ pkgs, inputs, ... }:
let
  hyprlandPkgs = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system};
  inherit (hyprlandPkgs) xdg-desktop-portal-hyprland;
in
{
  systemd.user.services.xdg-desktop-portal-hyprland = {
    Unit = {
      Description = "XDG Desktop Portal for Hyprland";
      Documentation = "https://github.com/hyprwm/xdg-desktop-portal-hyprland";
      After = [ "graphical-session.target" "xdg-desktop-portal.service" ];
      PartOf = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "dbus";
      BusName = "org.freedesktop.impl.portal.desktop.hyprland";
      ExecStart = "${xdg-desktop-portal-hyprland}/libexec/xdg-desktop-portal-hyprland";
      Restart = "on-failure";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}

