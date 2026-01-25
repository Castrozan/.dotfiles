{ pkgs, inputs, ... }:
let
  hyprlandFlake = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland;
in
{
  home.file.".config/hypr".source = ../../../.config/hypr;

  home.packages = [
    hyprlandFlake
  ];
}
