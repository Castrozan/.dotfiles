{ pkgs, ... }:
{
  home.packages = with pkgs; [
    tree
    bash
    bash-completion
    pavucontrol
    playerctl
    pulsemixer
    imv
  ];
}
