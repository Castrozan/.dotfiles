#!/usr/bin/env bash

# Aliases file for bash shell

# aliases personal
alias bashrc='nvim ~/.bashrc'
alias b='btop'
alias c='code'
alias cat='cat'
alias catt='bat'
alias claude='NIXPKGS_ALLOW_UNFREE=1 nix run github:k3d3/claude-desktop-linux-flake --impure > /dev/null 2>&1 &'
alias code='code . -n'
alias cu='cursor'
alias cursor='cursor . -n > /dev/null 2>&1 &'
alias d='lazydocker'
alias dotfiles='cd ~/.dotfiles'
alias g='lazygit'
alias grep='grep --color=auto'
alias i='idea'
alias idea='idea . > /dev/null 2>&1 &'
alias kc="nvim ~/.config/kitty/kitty.conf"
alias killport='sh $HOME/.local/bin/killport'
alias l='ls -CF'
alias la='ls -A'
alias lc='ls -a --color=never'
alias ll='ls -alF'
alias ls='ls --color=auto'
alias n='nvim'
alias obsidian='obsidian >/dev/null 2>&1 & disown'
alias oo='cd $OBSIDIAN_HOME'
alias repo='cd $HOME/repo'
alias run-endpoint-monitor='nix-shell $HOME/repo/notifications/shell.nix --run "python $HOME/repo/notifications/app.py"'
alias satc='cd $HOME/repo/satc'
alias scripts='cd $HOME/repo/scripts'
alias source-bash='source ~/.bashrc'
alias t='tmux attach -t screensaver 2>/dev/null || _start_tmux'
alias todo='cd $HOME/vault'
alias y='yazi'

# aliases for nixos
alias game-shift='sudo game-shift'
alias nord-off='sudo wgnord d'
alias nord-on-us='sudo wgnord c US'
alias rebuild='sudo nixos-rebuild switch --flake $HOME/.dotfiles/nixos#$(whoami)'
