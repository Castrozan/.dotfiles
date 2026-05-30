{ pkgs, inputs, ... }:
let
  hyprlandPkgs = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system};
  inherit (hyprlandPkgs) xdg-desktop-portal-hyprland;

  patchedHyprland = import ../../../lib/patched-hyprland.nix { inherit pkgs inputs; };

  hyprshot-fixed = pkgs.hyprshot.override {
    hyprland = patchedHyprland;
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
        swww
        libnotify
        pamixer
        bemoji
        hyprshot-fixed
        grim
        slurp
        wf-recorder
        cliphist
        hyprpicker
        hyprsunset
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
