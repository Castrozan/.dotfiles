#!/usr/bin/env bash

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

## BEGIN DEFINE GLOBAL VARIABLES

# Define default editor
export EDITOR=cursor

## END GLOBAL VARIABLES

# Function to start the first tmux session for screensaver
_start_screensaver_tmux_session() {
    # Check if the screensaver session exists
    if ! tmux has-session -t screensaver 2>/dev/null; then

        if command -v cmatrix &>/dev/null; then
            # Start cmatrix, bonsai and pipes as screensaver
            tmux new-session -d -s screensaver \; \
                rename-window 'screensaver' \; \
                send-keys 'bonsai_screensaver' C-m \; \
                split-window -h \; \
                send-keys 'pipes_screensaver' C-m \; \
                split-window -v \; \
                send-keys 'sleep 1; cmatrix' C-m
        else
            # Start bonsai and pipes as screensaver
            tmux new-session -d -s screensaver \; \
                rename-window 'screensaver' \; \
                send-keys 'bonsai_screensaver' C-m \; \
                split-window -h \; \
                send-keys 'pipes_screensaver' C-m
        fi
    fi
}

# Function to start a main tmux session
_start_main_tmux_session() {
    # Check if the main session exists
    if ! tmux has-session -t main 2>/dev/null; then
        tmux new-session -d -s main -n main
    fi
}

_start_tmux() {
    # Start tmux
    _start_screensaver_tmux_session
    _start_main_tmux_session
    tmux attach -t screensaver
}

# Open tmux sessions on startup
if command -v tmux &>/dev/null && \
   [ -n "$PS1" ] && \
   [[ ! "$TERM" =~ screen ]] && \
   [[ ! "$TERM" =~ tmux ]] && \
   [ -z "$TMUX" ] && \
   [[ $(ps -o comm= -p "$PPID") != "cursor" ]]; then
    _start_tmux
fi

# Check if the OS is NixOS
is_nixos() {
    grep -q "ID=nixos" /etc/os-release
}

# Check if is wsl session
is_wsl() {
    [ -f "/proc/sys/fs/binfmt_misc/WSLInterop" ]
}

# Set random background image in Kitty terminal only on NixOS
# TODO: some day this should be fixed
# I really like custom switching backgrounds
#if is_nixos; then
#    if ps aux | grep "[k]itty" >/dev/null; then
#        [ -n "$KITTY_WINDOW_ID" ] && set-random-bg-kitty
#    fi
#fi

# Source bash env vars config
if [ -f ~/.bash_env_vars ]; then
    # shellcheck source=.bash_env_vars
    . ~/.bash_env_vars
fi

# Source bash completion
if [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
fi

# BEGIN EVN VARIABLES
# Add local bin to PATH
export PATH=$PATH:~/.local/bin

# Neovim
# This exports is broken, it should be fixed
export PATH="$PATH:/opt/nvim-linux64/bin"

# asdf
# TODO: should i use asdf or pyenv and others?
# [ -f "$HOME/.asdf/asdf.sh" ] && . "$HOME/.asdf/asdf.sh"
# [ -f "$HOME/.asdf/completions/asdf.bash" ] && . "$HOME/.asdf/completions/asdf.bash"

# NVM variables
export NVM_DIR="$HOME/.nvm"
# This loads nvm
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
# This loads nvm bash_completion
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Pyenv variables
export PYENV_ROOT=$HOME/.pyenv
export PATH="$PYENV_ROOT/bin:$PATH"

# Obsidian
# Create valt if it doesn't exist
if [ ! -d "$HOME/vault" ]; then
    mkdir -p "$HOME/vault"
fi
# Set the path to the Obsidian vault
export OBSIDIAN_HOME="$HOME/vault"

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

# Java
# Set a default JAVA_HOME for devices
# Chose between sdkman and jbang
# Current ubuntu is using sdkman
# Add JBang to environment
# alias j!=jbang
# export PATH="$HOME/.jbang/bin:$HOME/.jbang/currentjdk/bin:$PATH"
# export JAVA_HOME=$HOME/.jbang/currentjdk

# Brew
# Add brew to PATH
# TODO: define a better way of setting os specific commands
if ! is_nixos; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi

# Terraform
# Set autocomplete for terraform
if ! is_nixos; then
    complete -C /usr/bin/terraform terraform
fi

# Set the default browser on WSL
if is_wsl; then
    export BROWSER='/mnt/c/Users/castr/AppData/Local/BraveSoftware/Brave-Browser/Application/brave.exe'
fi

# Check if clipse is installed and run clipse --listen if it is
# TODO: this should be properly implemented
if command -v clipse &>/dev/null; then
    clipse --listen
fi

# Files sourced by $HOME/.dotfiles
. $HOME/.dotfiles/shell/configs/bash_history.sh
. $HOME/.dotfiles/shell/configs/fzf_catppuccin_theme.sh
. $HOME/.dotfiles/shell/configs/fzf_bash_history.sh
. $HOME/.dotfiles/shell/configs/bash_aliases.sh
. $HOME/.dotfiles/shell/configs/zoxide.sh
. $HOME/.dotfiles/shell/configs/screensaver.sh
. $HOME/.dotfiles/shell/configs/default_directories.sh
