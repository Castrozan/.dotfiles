{ pkgs, ... }:
{
  home.file.".config/fuzzel".source = ../../.config/fuzzel;

  programs.fuzzel = {
    enable = true;
    package = pkgs.fuzzel;
  };
}
