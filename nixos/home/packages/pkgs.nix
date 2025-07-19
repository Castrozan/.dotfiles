{ pkgs, ... }:
{
  home.packages = with pkgs; [
    bash
    bash-completion
    imv
    pavucontrol
    playerctl
    pulsemixer
    tree
  ];
}
