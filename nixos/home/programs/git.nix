{ pkgs, ... }:
{
  home.packages = [ pkgs.gh ];

  programs.git = {
    enable = true;
    userName = "Castrozan";
    userEmail = "castro.lucas290@gmail.com";
  };
}
