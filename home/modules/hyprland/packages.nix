{ pkgs, inputs, ... }:
let
  xdg-desktop-portal-hyprland =
    inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland;
in
{
  home = {
    file.".config/hypr".source = ../../../.config/hypr;

    packages = with pkgs; [
      xdg-desktop-portal
      xdg-desktop-portal-hyprland
      xdg-desktop-portal-gtk

      wl-clipboard
      hyprpaper
      swaybg
      mako
      libnotify
      hyprlock
      hypridle
      playerctl
      pamixer
      swayosd
      bemoji
      hyprshot
      grim
      slurp
      satty
      wf-recorder
      cliphist
      hyprpicker
      jq
      wlogout
      polkit_gnome
      gnome-calculator
      yad
      blueman
      pavucontrol
    ];
  };

  xdg.configFile."xdg-desktop-portal/hyprland-portals.conf".text = ''
    [preferred]
    default=hyprland;gtk
    org.freedesktop.impl.portal.Screenshot=hyprland
    org.freedesktop.impl.portal.ScreenCast=hyprland
    org.freedesktop.impl.portal.Inhibit=none
  '';
}
