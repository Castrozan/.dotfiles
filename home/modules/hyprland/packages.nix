{ pkgs, inputs, ... }:
let
  hyprlandPkgs = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system};
  inherit (hyprlandPkgs) xdg-desktop-portal-hyprland;

  # Override hyprshot to use correct hyprland version (nixpkgs bundles old hyprctl)
  hyprshot-fixed = pkgs.hyprshot.override {
    hyprland = hyprlandPkgs.hyprland;
  };
in
{
  home = {
    file.".config/hypr".source = ../../../.config/hypr;
    file.".config/swaync".source = ../../../.config/swaync;

    packages = with pkgs; [
      xdg-desktop-portal
      xdg-desktop-portal-hyprland
      xdg-desktop-portal-gtk

      wl-clipboard
      hyprpaper
      swaybg
      libnotify
      hyprlock
      hypridle
      playerctl
      pamixer
      swayosd
      bemoji
      hyprshot-fixed
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
