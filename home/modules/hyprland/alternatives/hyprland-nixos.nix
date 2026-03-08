{ pkgs, inputs, ... }:
let
  hyprlandFlake = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland;
in
{
  home.packages = [ hyprlandFlake ];
}
