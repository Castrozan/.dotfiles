{ pkgs, ... }:
{
  home.file.".config/hypr".source = ../../../.config/hypr;

  home.packages = with pkgs; [
    wezterm
  ];
}
