{ pkgs, inputs, ... }:
let
  hyprlandFlake = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland;
in
{
  home = {
    file.".config/hypr".source = ../../../.config/hypr;

    packages = [
      hyprlandFlake
    ]
    ++ (with pkgs; [
      # FIRST HALF - binary search
      wl-clipboard
      hyprpaper
      swaybg
      mako
      libnotify
      playerctl
      pamixer
      swayosd
      bemoji
    ]);
  };
}
