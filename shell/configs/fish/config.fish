set fish_greeting

# Enable autosuggestions
set -g fish_autosuggestion_enabled 1

# Portable environment setup
source ~/.dotfiles/shell/configs/fish/bass_env.fish

# Fish-specific components
source ~/.dotfiles/shell/configs/fish/conf.d/tmux.fish
source ~/.dotfiles/shell/configs/fish/conf.d/aliases.fish
source ~/.dotfiles/shell/configs/fish/conf.d/fzf.fish
source ~/.dotfiles/shell/configs/fish/conf.d/nvm.fish
source ~/.dotfiles/shell/configs/fish/conf.d/default_directories.fish
source ~/.dotfiles/shell/configs/fish/conf.d/key_bindings.fish

# Functions
source ~/.dotfiles/shell/configs/fish/functions/fish_prompt.fish
source ~/.dotfiles/shell/configs/fish/functions/screensaver.fish
source ~/.dotfiles/shell/configs/fish/functions/cursor.fish
source ~/.dotfiles/shell/configs/fish/functions/sdk.fish

zoxide init fish | source
