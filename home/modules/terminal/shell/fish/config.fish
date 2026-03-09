set fish_greeting

# Enhanced autosuggestions configuration
set -g fish_autosuggestion_enabled 1
set -g fish_autosuggestion_accept_on_space 0
set -g fish_autosuggestion_accept_on_tab 0

# Use command history and valid file paths for suggestions
set -g fish_autosuggestion_strategy history match_previous

# Faster completions with paging
set -g fish_complete_inline_descriptions yes
set -g fish_pager_color_completion normal
set -g fish_pager_color_description 555 yellow
set -g fish_pager_color_prefix cyan --underline
set -g fish_pager_color_progress cyan

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

zoxide init fish | source
