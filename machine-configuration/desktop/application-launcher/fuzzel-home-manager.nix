{ pkgs, ... }:
{
  home.file.".config/fuzzel".source = ./program-configuration/fuzzel;

  programs.fuzzel = {
    enable = true;
    package = pkgs.fuzzel;
  };
}
