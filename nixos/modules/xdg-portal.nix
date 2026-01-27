{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.custom.xdgPortal;
in
{
  options.custom.xdgPortal = {
    enable = lib.mkEnableOption "XDG portal routing for Hyprland/GNOME coexistence";
  };

  config = lib.mkIf cfg.enable {
    xdg.portal = {
      enable = true;
      extraPortals = [ pkgs.xdg-desktop-portal-gtk ];
      config = {
        Hyprland = {
          default = [
            "hyprland"
            "gtk"
          ];
          "org.freedesktop.impl.portal.Screenshot" = "hyprland";
          "org.freedesktop.impl.portal.ScreenCast" = "hyprland";
        };
        GNOME = {
          default = [
            "gnome"
            "gtk"
          ];
        };
      };
    };
  };
}
