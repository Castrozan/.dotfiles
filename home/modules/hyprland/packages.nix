{ pkgs, inputs, ... }:
let
  hyprlandPkgs = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system};
  inherit (hyprlandPkgs) xdg-desktop-portal-hyprland;

  hyprshot-fixed = pkgs.hyprshot.override {
    inherit (hyprlandPkgs) hyprland;
  };
in
{
  imports = [ ./xwayland-with-auth.nix ];

  home = {
    packages =
      with pkgs;
      [
        xdg-desktop-portal
        xdg-desktop-portal-gtk

        wl-clipboard
        hyprpaper
        swaybg
        libnotify
        pamixer
        bemoji
        hyprshot-fixed
        grim
        slurp
        wf-recorder
        cliphist
        hyprpicker
        jq
        yq-go
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
}
