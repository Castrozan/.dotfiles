{ pkgs, inputs, ... }:
let
  hyprlandFlake = import ../../../../lib/patched-hyprland.nix { inherit pkgs inputs; };
in
{
  home.packages = [ hyprlandFlake ];
}
