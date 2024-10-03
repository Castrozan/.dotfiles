#!/bin/bash

# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# If not running interactively, don't do anything
case $- in
*i*) ;;
*) return ;;
esac

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.
#shopt -s globstar

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
xterm-color | *-256color) color_prompt=yes ;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
#force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
        # We have color support; assume it's compliant with Ecma-48
        # (ISO/IEC-6429). (Lack of such support is extremely rare, and such
        # a case would tend to support setf rather than setaf.)
        color_prompt=yes
    else
        color_prompt=
    fi
fi

# Show current git branch in prompt
parse_git_branch() {
    git branch 2>/dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
}

# Define PS1
if [ "$color_prompt" = yes ]; then
    PS1="\[\033[01;32m\] \u\[\033[00m\]\[\033[01;34m\] \W\[\033[00m\]\[\033[01;1;38;2;253;200;169m\]\$(parse_git_branch)\[\033[00m\]\$ "
else
    PS1="\u@\h:\w\$(parse_git_branch)\$ "
fi

unset color_prompt force_color_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm* | rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@: \W\a\]$PS1"
    ;;
*) ;;
esac

# Creates a screensaver with pipes and bonsai
_start_first_tmux_session() {
    # Check if any tmux session exists
    if ! tmux has-session 2>/dev/null; then
        # Start tmux and split panes
        tmux new-session -d -s 1 \; \
            rename-window 'screensaver' \; \
            send-keys 'bonsai_screensaver' C-m \; \
            split-window -h \; \
            send-keys 'pipes_screensaver' C-m \; \
            attach
    else
        tmux attach -t 1
    fi
}

# Open tmux on startup
if command -v tmux &>/dev/null && [ -n "$PS1" ] && [[ ! "$TERM" =~ screen ]] && [[ ! "$TERM" =~ tmux ]] && [ -z "$TMUX" ]; then
    _start_first_tmux_session
fi

# Source aliases
if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# Source bash env vars config
if [ -f ~/.bash_env_vars ]; then
    . ~/.bash_env_vars
fi

# Source bash completion
if [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
fi

# Create repo directory if it doesn't exist
if [ ! -d "$HOME/repo" ]; then
    mkdir -p "$HOME/repo"
fi

# Create fonts directory if it doesn't exist
if [ ! -d "$HOME/.local/share/fonts" ]; then
    mkdir -p "$HOME/.local/share/fonts"
fi

# Experimental
# Set caps lock to escape
setxkbmap -option caps:escape

# BEGIN EVN VARIABLES
# Add local bin to PATH
export PATH=$PATH:~/.local/bin

# Neovim
# This exports is broken, it should be fixed
export PATH="$PATH:/opt/nvim-linux64/bin"

# asdf
[ -f "$HOME/.asdf/asdf.sh" ] && . "$HOME/.asdf/asdf.sh"
[ -f "$HOME/.asdf/completions/asdf.bash" ] && . "$HOME/.asdf/completions/asdf.bash"

# NVM variables
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"                   # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" # This loads nvm bash_completion

# Pyenv variables
export PYENV_ROOT=$HOME/.pyenv
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
export PATH="$HOME/.pyenv/bin:$PATH"

# Obsidian
# Create valt if it doesn't exist
if [ ! -d "$HOME/Documents/obsidianVault" ]; then
    mkdir -p "$HOME/Documents/obsidianVault"
fi
# Set the path to the Obsidian vault
export OBSIDIAN_HOME="$HOME/Documents/obsidianVault"

# flatpak
export XDG_DATA_DIRS=/var/lib/flatpak/exports/share:$HOME/.local/share/flatpak/exports/share:$XDG_DATA_DIRS

# pnpm
export PNPM_HOME="$HOME/.local/share/pnpm"
case ":$PATH:" in
*":$PNPM_HOME:"*) ;;
*) export PATH="$PNPM_HOME:$PATH" ;;
esac

# Sdkman
export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && source "$HOME/.sdkman/bin/sdkman-init.sh"

# flatpak
export XDG_DATA_DIRS=/var/lib/flatpak/exports/share:$HOME/.local/share/flatpak/exports/share:$XDG_DATA_DIRS

# pnpm
export PNPM_HOME="$HOME/.local/share/pnpm"
case ":$PATH:" in
*":$PNPM_HOME:"*) ;;
*) export PATH="$PNPM_HOME:$PATH" ;;
esac

# fzf
[ -f $HOME/.fzf.bash ] && . $HOME/.fzf.bash

# Terraform
# Set autocomplete for terraform
complete -C /usr/bin/terraform terraform

# Brew
# Add brew to PATH
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

# Files sourcered by $HOME/.dotfiles
. $HOME/.dotfiles/shell/configs/bash_history.sh
. $HOME/.dotfiles/shell/configs/fzf.sh
. $HOME/.dotfiles/shell/configs/fzf_bash_history.sh
. $HOME/.dotfiles/shell/configs/git_aliases.sh
. $HOME/.dotfiles/shell/configs/zoxide.sh
