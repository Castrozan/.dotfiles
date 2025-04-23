{ pkgs, ... }:
{
  imports = [
    ./wlogout.nix
  ];

  home.file.".config/hypr".source = ../../../.config/hypr;
  home.file.".config/waybar".source = ../../../.config/waybar;

  # Hyprland packages
  home.packages = with pkgs; [
    swaylock-effects
    swww
    xclip
    wl-clipboard
    gnome-tweaks
    playerctl
    pamixer
    mako
    libnotify
    glib
    dunst

    waybar
    hyprlock
    hyprpaper
    wlogout
  ];
}
