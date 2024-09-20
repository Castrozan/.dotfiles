#!/bin/bash

# Aliases file for bash shell

# aliases personal
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias code='code . -n'
alias lc='ls -a --color=never'
alias oo='cd $OBSIDIAN_HOME'
alias studio3t='cd ~/studio3t && ./Studio-3T .sh'
alias bashrc='nvim ~/.bashrc'
alias repo='cd $HOME/repo'
alias dotfiles='cd ~/.dotfiles_ubuntu'
alias source-bash='source ~/.bashrc'
alias obsidian='flatpak run md.obsidian.Obsidian >/dev/null 2>&1 &'
alias t='tmux attach -t 1 || _start_first_tmux_session'
alias y='yazi'
alias todo='cd $HOME/Documents/obsidianVault && nvim TODO.md'
alias scripts='cd $HOME/repo/scripts && nvim .'
alias g='lazygit'
alias d='lazydocker'
alias killport='sh $HOME/.local/bin/killport'
alias pipes='$HOME/repo/pipes.sh/pipes.sh'
alias bonsai='$HOME/repo/cbonsai/cbonsai -l -i -b 1 -c mWm,wMw,mMw,wWm -M 3 -L 40'
