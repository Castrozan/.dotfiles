{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  hyprlandPkgs = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system};
  inherit (hyprlandPkgs) xdg-desktop-portal-hyprland;

  nixGLIntel = inputs.nixgl.packages.${pkgs.stdenv.hostPlatform.system}.nixGLIntel;

  xdphExecStart =
    if isNixOS then
      "${xdg-desktop-portal-hyprland}/libexec/xdg-desktop-portal-hyprland"
    else
      "${nixGLIntel}/bin/nixGLIntel ${xdg-desktop-portal-hyprland}/libexec/xdg-desktop-portal-hyprland";
in
{
  systemd.user.services.xdg-desktop-portal-hyprland = {
    Unit = {
      Description = "XDG Desktop Portal for Hyprland";
      Documentation = "https://github.com/hyprwm/xdg-desktop-portal-hyprland";
      After = [
        "graphical-session.target"
        "xdg-desktop-portal.service"
      ];
      PartOf = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "dbus";
      BusName = "org.freedesktop.impl.portal.desktop.hyprland";
      ExecStart = xdphExecStart;
      Restart = "on-failure";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
