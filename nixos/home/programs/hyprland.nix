{ pkgs, ... }:
{
  imports = [
    ./wlogout.nix
  ];

  home.file.".config/hypr".source = ../../../.config/hypr;

  # Hyprland packages
  home.packages = with pkgs; [
    swaylock-effects
    swww
    xclip
    wl-clipboard
    gnome-tweaks

    waybar
    hyprlock
    hyprpaper
    wlogout
  ];
}
