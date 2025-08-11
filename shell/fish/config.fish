set fish_greeting

# Enable autosuggestions
set -g fish_autosuggestion_enabled 1

# Portable environment setup
source ~/.dotfiles/shell/fish/bass_env.fish

# Fish-specific components
source ~/.dotfiles/shell/fish/conf.d/tmux.fish
source ~/.dotfiles/shell/fish/conf.d/aliases.fish
source ~/.dotfiles/shell/fish/conf.d/fzf.fish
source ~/.dotfiles/shell/fish/conf.d/nvm.fish
source ~/.dotfiles/shell/fish/conf.d/default_directories.fish
source ~/.dotfiles/shell/fish/conf.d/key_bindings.fish

# Functions
source ~/.dotfiles/shell/fish/functions/fish_prompt.fish
source ~/.dotfiles/shell/fish/functions/screensaver.fish
source ~/.dotfiles/shell/fish/functions/cursor.fish
source ~/.dotfiles/shell/fish/functions/sdk.fish

zoxide init fish | source
