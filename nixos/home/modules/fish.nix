{ pkgs, ... }:
let
  shellInit = builtins.readFile ../../../shell/configs/fish/config.fish;
in
{
  programs.fish = {
    enable = true;
    package = pkgs.fish;
    interactiveShellInit = ''${shellInit}'';
    plugins = [
      { name = "bass"; src = pkgs.fishPlugins.bass; }
      { name = "fzf-fish"; src = pkgs.fishPlugins.fzf-fish; }
    ];
  };
}
