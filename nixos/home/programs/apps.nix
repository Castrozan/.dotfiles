{ pkgs, ... }:

{
  # Nix packages to install for the user
  home.packages = with pkgs; [
    tree
  ];
}
