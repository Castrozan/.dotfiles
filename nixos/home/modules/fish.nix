{ pkgs, ... }:
{
  programs.fish = {
    enable = true;
    package = pkgs.fish;
    shellAliases = {
      ls = "eza --icons=always";
      ll = "eza --icons=always -l";
      la = "eza --icons=always -la";
    };
  };
}
