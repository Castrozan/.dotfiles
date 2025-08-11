{ pkgs, ... }:
{
  home.packages = with pkgs; [
    imv
    pavucontrol
    playerctl
    pulsemixer
    tree
  ];
}
