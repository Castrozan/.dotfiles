#!/usr/bin/env bash

# Zoxide
if command -v zoxide &>/dev/null; then
    # TODO: add alias cd to zoxide after training
    # eval "$(zoxide init --cmd cd bash)"
    eval "$(zoxide init bash)"
    # fzf integration and theme
    export _ZO_FZF_OPTS="--height 40% \
    --layout=reverse --border --preview='command -p ls -ACp \
    --color=always --group-directories-first {2..}' \
    --preview-window=right,50%,sharp \
    --color=bg+:#313244,bg:#1e1e2e,spinner:#f5e0dc,hl:#f38ba8 \
    --color=fg:#cdd6f4,header:#f38ba8,info:#cba6f7,pointer:#f5e0dc \
    --color=marker:#b4befe,fg+:#cdd6f4,prompt:#cba6f7,hl+:#f38ba8 \
    --color=selected-bg:#45475a \
    --multi"
fi
