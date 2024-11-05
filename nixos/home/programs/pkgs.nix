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

    dolphin
  ];
}
