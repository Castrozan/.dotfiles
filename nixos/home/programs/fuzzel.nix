{ pkgs, ... }:
{
  programs.fuzzel = {
    enable = true;
    package = pkgs.fuzzel;
  };

  home.file.".config/fuzzel".source = ../../../.config/fuzzel;
}
