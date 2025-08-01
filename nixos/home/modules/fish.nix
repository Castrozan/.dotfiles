{ pkgs, ... }:
{
  programs.fish = {
    enable = true;
    package = pkgs.fish;
  };

  # Link the new fish config files to the correct location
  #   home.file.".config/fish/config.fish".source = ../../../shell/configs/fish/config.fish;
  home.file.".config/fish/bass_env.fish".source = ../../../shell/configs/fish/bass_env.fish;
  home.file.".config/fish/conf.d/tmux.fish".source = ../../../shell/configs/fish/conf.d/tmux.fish;
  home.file.".config/fish/functions/fish_prompt.fish".source =
    ../../../shell/configs/fish/functions/fish_prompt.fish;
}
