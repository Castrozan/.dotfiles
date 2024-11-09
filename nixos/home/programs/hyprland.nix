{ pkgs, ... }:
{
  home.file.".config/hypr".source = ../../../.config/hypr;

  # Hyprland packages
  home.packages = with pkgs; [
    swaylock-effects
    swww
    xclip
    wl-clipboard
    gnome.gnome-tweaks

    waybar
  ];
}
