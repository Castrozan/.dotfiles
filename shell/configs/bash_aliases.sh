#!/bin/bash

# Aliases file for bash shell

# aliases personal
alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias code='code . -n'
alias c='code'
alias lc='ls -a --color=never'
alias oo='cd $OBSIDIAN_HOME'
alias studio3t='cd ~/studio3t && ./Studio-3T .sh'
alias bashrc='nvim ~/.bashrc'
alias repo='cd $HOME/repo'
alias satc='cd $HOME/repo/satc'
alias dotfiles='cd ~/.dotfiles'
alias satc='cd ~/repo/satc'
alias source-bash='source ~/.bashrc'
alias obsidian='flatpak run md.obsidian.Obsidian >/dev/null 2>&1 &'
alias t='tmux attach -t screensaver 2>/dev/null || _start_tmux'
alias y='yazi'
alias todo='cd $HOME/Documents/obsidianVault && nvim TODO.md'
alias scripts='cd $HOME/repo/scripts && nvim .'
alias g='lazygit'
alias d='lazydocker'
alias killport='sh $HOME/.local/bin/killport'
alias kc="nvim ~/.config/kitty/kitty.conf"

# aliases for nixos
alias rebuild='sudo nixos-rebuild switch --flake $HOME/.dotfiles/nixos#$(whoami)'
alias nord-on-us='sudo wgnord c US'
alias nord-off='sudo wgnord d'
