{ pkgs, ... }:
let
  shellInit = builtins.readFile ../../../shell/configs/fish/config.fish;
in
{
  home.packages = with pkgs; [
    fishPlugins.bass # For running bash scripts in fish
    fishPlugins.fzf-fish
  ];

  programs.fish = {
    enable = true;
    package = pkgs.fish;
    interactiveShellInit = ''${shellInit}'';
  };
}
