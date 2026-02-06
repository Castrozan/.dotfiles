set fish_greeting

# Enable autosuggestions
set -g fish_autosuggestion_enabled 1

# Add cargo bin to PATH
fish_add_path ~/.cargo/bin

# TODO: this should be sourced from a lucas.zanoni specific file on it's config dir
# NSS library preload for corporate authentication (required for devenv)
# Only set for lucas.zanoni user
if test "$USER" = "lucas.zanoni"
    set -x LD_PRELOAD '/lib/x86_64-linux-gnu/libnss_sss.so.2'
end

if command -v clipse &>/dev/null
    # clipse --listen is long-running; background it so shell startup is not blocked.
    if not pgrep -x clipse >/dev/null 2>&1
        nohup clipse --listen >/dev/null 2>&1 &
        disown
    end
end

# Portable environment setup
source ~/.dotfiles/shell/fish/bass_env.fish

# Fish-specific components
source ~/.dotfiles/shell/fish/conf.d/tmux.fish
source ~/.dotfiles/shell/fish/conf.d/aliases.fish
source ~/.dotfiles/shell/fish/conf.d/fzf.fish
source ~/.dotfiles/shell/fish/conf.d/default_directories.fish
source ~/.dotfiles/shell/fish/conf.d/key_bindings.fish

# Functions
source ~/.dotfiles/shell/fish/functions/fish_prompt.fish
source ~/.dotfiles/shell/fish/functions/cursor.fish

zoxide init fish | source
