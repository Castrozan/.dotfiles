set fish_greeting

# Portable environment setup
source ~/.dotfiles/shell/configs/fish/bass_env.fish

# Fish-native components
source ~/.dotfiles/shell/configs/fish/conf.d/tmux.fish
source ~/.dotfiles/shell/configs/fish/conf.d/aliases.fish
source ~/.dotfiles/shell/configs/fish/conf.d/fzf.fish
source ~/.dotfiles/shell/configs/fish/conf.d/default_directories.fish
zoxide init fish | source