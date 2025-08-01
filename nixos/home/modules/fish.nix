{ pkgs, ... }:
{
  programs.fish = {
    enable = true;
    package = pkgs.fish;
    extraConfig = builtins.readFile ../../../shell/configs/fish/config.fish;
  };

  # Link the new fish config files to the correct location
  # home.file.".config/fish/config.fish".source is not needed due to extraConfig
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
