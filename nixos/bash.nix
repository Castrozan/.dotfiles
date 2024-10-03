{ pkgs, ... }:
{
  # Global Bash configuration
  environment.etc."bashrc".text = ''
    # ~/.bashrc: executed by bash(1) for non-login shells.

    # If not running interactively, don't do anything
    case $- in
        *i*) ;;
          *) return;;
    esac

    # Don't put duplicate lines or lines starting with space in the history.
    HISTCONTROL=ignoreboth

    # Append to the history file, don't overwrite it
    shopt -s histappend

    # Set history length
    HISTSIZE=1000
    HISTFILESIZE=2000

    # Check the window size after each command and, if necessary,
    # update the values of LINES and COLUMNS.
    shopt -s checkwinsize

    # Make less more friendly for non-text input files
    [ -x "$(command -v lesspipe)" ] && eval "$(SHELL=/bin/sh lesspipe)"

    # Set a fancy prompt (non-color, unless we know we "want" color)
    case "$TERM" in
        xterm-color|*-256color) color_prompt=yes;;
    esac

    # Show current git branch in prompt
    parse_git_branch() {
        git branch 2>/dev/null | grep -e '^*' | sed 's/* \(.*\)/ (\1)/'
    }

    if [ "$color_prompt" = yes ]; then
        PS1="\[\e]0;\u@\h: \w\007\]\[\033[01;32m\]\u\[\033[00m\]\[\033[01;34m\] \W\[\033[00m\]\[\033[01;1;38;2;253;200;169m\]\$(parse_git_branch)\[\033[00m\]\$ "
    else
        PS1='\u@\h:\w\$(parse_git_branch)\$ '
    fi
    unset color_prompt

    # If this is an xterm set the title to user@host:dir
    case "$TERM" in
    xterm*|rxvt*)
        PS1="\[\e]0\u@\h: \W\a\]$PS1"
        ;;
    *)
        ;;
    esac

    # Enable color support of ls and also add handy aliases
    if [ -x "$(command -v dircolors)" ]; then
        test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
        alias ls='ls --color=auto'
        alias grep='grep --color=auto'
        alias fgrep='fgrep --color=auto'
        alias egrep='egrep --color=auto'
    fi

    # BEGIN ENV VARIABLES
    export OBSIDIAN_HOME="$HOME/obsidianVault"
    export EDITOR="code"
    # END ENV VARIABLES

    # BEGIN ALIASES

    # aliases personal
    alias ll='ls -alF'
    alias la='ls -A'
    alias l='ls -CF'
    alias oo="cd $OBSIDIAN_HOME"
    alias lc="ls -a --color=never"
    alias dotfiles="cd ~/.dotfiles-nixos"
    alias rebuild="sudo nixos-rebuild switch --flake /home/zanoni/.dotfiles-nixos#zanoni --impure"
    alias t="tmux"
    alias todo="code $OBSIDIAN_HOME -g $OBSIDIAN_HOME/TODO.md"
    alias g="lazygit"
    alias d="lazydocker"
    alias nvm="nvim"
    alias vnm="nvim"
    alias v="nvim"
    alias kc="nvim ~/.config/kitty/kitty.conf"
    alias repo="cd ~/repo"
    alias code="code . -n"
    # END ALIASES

    # BEGIN CASE INSENSITIVE TAB COMPLETION
    # If ~/.inputrc doesn't exist yet: First include the original /etc/inputrc
    # so it won't get overriden
    if [ ! -a ~/.inputrc ]; then echo '$include /etc/inputrc' > ~/.inputrc; fi

    # Add shell-option to ~/.inputrc to enable case-insensitive tab completion
    echo 'set completion-ignore-case On' >> ~/.inputrc
    # END CASE INSENSITIVE TAB COMPLETION

    # BEGIN GIT ALIASES
    alias gs='git status'
    alias gd='git diff'
    alias gl='git log'
    alias gc='git checkout'
    alias gp='git push'
    alias gpl='git pull'
    alias gadd='git add .'
    alias dotcommit="git add . && git commit -m '.'"
    # END GIT ALIASES

    # Set random background image in Kitty terminal
    if ps aux | grep "[k]itty" > /dev/null; then
        [ -n "$KITTY_WINDOW_ID" ] && set-random-bg-kitty
    fi

    # Launch Steam in offload mode
    export XDG_DATA_HOME="$HOME/.local/share"

    # Ensure Steam runs with NVIDIA GPU offloading
    mkdir -p "$XDG_DATA_HOME/applications"
    sed 's/^Exec=/&nvidia-offload /' /run/current-system/sw/share/applications/steam.desktop > "$XDG_DATA_HOME/applications/steam.desktop"
  '';
}
