# Hyprland for NixOS - uses flake input directly
# NixOS provides GPU drivers via hardware.opengl and programs.hyprland.enable
{ pkgs, inputs, ... }:
let
  hyprlandFlake = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland;
in
{
  home.packages = [ hyprlandFlake ];
}
