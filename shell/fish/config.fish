set fish_greeting

# Enable autosuggestions
set -g fish_autosuggestion_enabled 1

# TODO: this should be sourced from a lucas.zanoni specific file on it's config dir
# NSS library preload for corporate authentication (required for devenv)
# Only set for lucas.zanoni user
if test "$USER" = "lucas.zanoni"
    set -x LD_PRELOAD '/lib/x86_64-linux-gnu/libnss_sss.so.2'
end

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
