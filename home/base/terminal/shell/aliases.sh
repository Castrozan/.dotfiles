#!/usr/bin/env bash

# Enable alias expansion in non-interactive shells (for Claude Code BASH_ENV)
shopt -s expand_aliases

# NixOS setuid wrappers (sudo, ping, etc) — non-login shells miss this
[[ -d /run/wrappers/bin ]] && [[ ":$PATH:" != *":/run/wrappers/bin:"* ]] && export PATH="/run/wrappers/bin:$PATH"

# Personal aliases
alias clebr='cd $HOME/.clebr'
alias bashrc='nvim ~/.bashrc'
alias b='btop'
alias c='code'
alias ca='claude-workspace'
alias cl='claude-workspace'
alias cla='claude-workspace'
alias cal='claude-workspace'
alias clau='claude-workspace'
alias claud='claude-workspace'
alias claude='claude-workspace'
alias lca='claude-workspace'
alias co='codex'
alias cat='cat'
alias catt='bat'
alias cd.='cd ..'
alias cd..='cd ..'
alias code='code . -n'
. "$HOME/.dotfiles/home/base/terminal/shell/cursor.sh"
alias d='lazydocker'
alias dotfiles='cd ~/.dotfiles'
alias g='lazygit'
alias gc='nix-gc'
alias game-shift='sudo game-shift'
alias grep='grep --color=auto'
alias h='herdr-screensaver'
alias i='idea . > /dev/null 2>&1 & disown'
alias k='k9s'
alias kc="nvim ~/.config/kitty/kitty.conf"
alias l='eza --classify'
alias la='eza --all'
alias lc='eza --all --color=never'
alias ll='eza --long --all --classify --git --icons'
alias ls='eza --color=auto'
alias lt='eza --tree --level=2 --icons'
alias n='nvim'
alias obsidian='obsidian >/dev/null 2>&1 & disown'
alias oo='cd $OBSIDIAN_HOME'
alias repo='cd $HOME/repo'
alias rga-fzf='rga-fzf'
alias run-endpoint-monitor='nix-shell $HOME/repo/notifications/shell.nix --run "python $HOME/repo/notifications/app.py"'
alias satc='cd $HOME/repo/satc'
alias scripts='cd $HOME/repo/scripts'
alias source-shell='source ~/.bashrc'
alias t='tmux attach || tmux'
alias todo='cd $HOME/vault'
alias vial='Vial'
alias workbench='cd $HOME/workbench || $EDITOR $HOME/workbench'
alias y='yazi'
# TODO: fix vivaldi, it should not be running as flatpak
alias vivaldi="flatpak run com.vivaldi.Vivaldi"

PRIVATE_SHELL_ALIASES="$HOME/.dotfiles/private-config/shell/aliases.sh"
# shellcheck disable=SC1090
if [ -f "$PRIVATE_SHELL_ALIASES" ]; then
	. "$PRIVATE_SHELL_ALIASES"
fi
