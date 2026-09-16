{ pkgs, inputs, ... }:
let
  hyprlandFlake = import ../build/patched-hyprland.nix { inherit pkgs inputs; };
in
{
  home.packages = [ hyprlandFlake ];
}
