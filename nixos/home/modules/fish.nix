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

  home.file.".config/fish/bass_env.fish".source = ../../../shell/configs/fish/bass_env.fish;
  home.file.".config/fish/conf.d/tmux.fish".source = ../../../shell/configs/fish/conf.d/tmux.fish;
  home.file.".config/fish/conf.d/fzf.fish".source = ../../../shell/configs/fish/conf.d/fzf.fish;
  home.file.".config/fish/conf.d/aliases.fish".source =
    ../../../shell/configs/fish/conf.d/aliases.fish;
  home.file.".config/fish/conf.d/default_directories.fish".source =
    ../../../shell/configs/fish/conf.d/default_directories.fish;
  home.file.".config/fish/functions/fish_prompt.fish".source =
    ../../../shell/configs/fish/functions/fish_prompt.fish;
  home.file.".config/fish/functions/screensaver.fish".source =
    ../../../shell/configs/fish/functions/screensaver.fish;
}
