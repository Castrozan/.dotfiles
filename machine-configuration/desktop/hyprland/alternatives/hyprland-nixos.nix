{ pkgs, inputs, ... }:
let
  hyprlandFlake = import ../patched-hyprland.nix { inherit pkgs inputs; };
in
{
  home.packages = [ hyprlandFlake ];
}
