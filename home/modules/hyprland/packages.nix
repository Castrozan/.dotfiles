{ pkgs, inputs, ... }:
let
  hyprlandPkgs = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system};
  inherit (hyprlandPkgs) xdg-desktop-portal-hyprland;

  # Override hyprshot to use correct hyprland version (nixpkgs bundles old hyprctl)
  hyprshot-fixed = pkgs.hyprshot.override {
    inherit (hyprlandPkgs) hyprland;
  };
in
{
  imports = [ ./xwayland-with-auth.nix ];

  home = {
    file.".config/hypr".source = ../../../.config/hypr;

    packages =
      with pkgs;
      [
        xdg-desktop-portal
        xdg-desktop-portal-gtk

        wl-clipboard
        hyprpaper
        swaybg
        libnotify
        # hyprlock — installed via programs.hyprlock.enable in NixOS for DRM/PAM perms

        pamixer
        bemoji
        hyprshot-fixed
        grim
        slurp
        wf-recorder
        cliphist
        hyprpicker
        jq
        wlogout
        polkit_gnome
        gnome-calculator
        yad
        blueman
      ]
      ++ [
        xdg-desktop-portal-hyprland
      ];
  };

  xdg.configFile = {
    # Mako config is generated from template in .config/hypr/templates/mako.conf.tpl

    "xdg-desktop-portal/hyprland-portals.conf".text = ''
      [preferred]
      default=hyprland;gtk
      org.freedesktop.impl.portal.Screenshot=hyprland
      org.freedesktop.impl.portal.ScreenCast=hyprland
      org.freedesktop.impl.portal.Inhibit=none
    '';
  };
}
