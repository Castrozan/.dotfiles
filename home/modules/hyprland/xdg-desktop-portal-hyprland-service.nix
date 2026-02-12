{
  pkgs,
  lib,
  inputs,
  isNixOS,
  ...
}:
let
  hyprlandPkgs = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system};
  inherit (hyprlandPkgs) xdg-desktop-portal-hyprland;

  inherit (inputs.nixgl.packages.${pkgs.stdenv.hostPlatform.system}) nixGLIntel;

  systemPipewireLibPath = "/usr/lib/x86_64-linux-gnu";

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
      Restart = "always";
      RestartSec = "1s";
    }
    // lib.optionalAttrs (!isNixOS) {
      Environment = "LD_PRELOAD=${systemPipewireLibPath}/libpipewire-0.3.so.0";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };

  systemd.user.services.xdg-desktop-portal = lib.mkIf (!isNixOS) {
    Unit = {
      Description = "Portal service (Nix)";
      After = [ "graphical-session.target" ];
      PartOf = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "dbus";
      BusName = "org.freedesktop.portal.Desktop";
      ExecStart = "${pkgs.xdg-desktop-portal}/libexec/xdg-desktop-portal";
      Restart = "on-failure";
      RestartSec = "1s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
