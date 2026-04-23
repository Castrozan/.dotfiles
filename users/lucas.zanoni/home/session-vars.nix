{ pkgs, ... }:
{
  home.sessionVariables = {
    OBSIDIAN_HOME = "$HOME/vault";
    EDITOR = "code";
    TZDIR = "${pkgs.tzdata}/share/zoneinfo";
  };
}
