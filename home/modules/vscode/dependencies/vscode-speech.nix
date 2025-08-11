{ pkgs, ... }:
{
  home.packages = with pkgs; [
    alsa-lib
  ];
}
