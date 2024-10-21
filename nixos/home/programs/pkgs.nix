#
# /nixos/home/programs/apps.nix
# Home manager pkgs
#
{ pkgs, ... }:
{
  home.packages = with pkgs; [
    tree
    bash
    bash-completion

    # wm - hyprland
    swaylock-effects
    swww
    xclip
    wl-clipboard
    gnome.gnome-tweaks
  ];
}
