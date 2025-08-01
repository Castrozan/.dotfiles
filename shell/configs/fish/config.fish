# ~/.config/fish/config.fish
if status is-interactive
  # Portable environment setup
  source ~/.dotfiles/shell/configs/fish/bass_env.fish

  # Fish-native components
  # source ~/.dotfiles/shell/configs/fish/conf.d/tmux.fish
  # zoxide init fish | source
end
