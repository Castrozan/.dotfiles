#!/usr/bin/env bash

# This file is set for you to chose pkgs and configs that you want to install
# That way you can declaratively set up your system
# There are 2 types of configurations:
# _DOTFILES_PACKAGES_TO_INSTALL: These are packages that you want to install
# _DOTFILES_SCRIPTS_TO_INSTALL: These are scripts that you want to install
# _DOTFILES_CONFIGS_TO_INSTALL: These are configurations that you want to set up
# Now it shows all packages and configs that are available
# Comment out any you don't want to install.

# Packages
PACKAGES=(
    bash_completion
    bat
    btop
    cbonsai
    clipse
    fzf
    # kitty
    lazygit
    neofetch
    neovim
    # nix
    nodejs
    npm
    nvm
    obsidian
    fira_code
    pipes
    tmux
    vim
    yazi
    zoxide
    zsh
)
# Scripts
SCRIPTS=(
    daily_note
    git_fzf
    killport
    on
    pybase
)

# Configs
CONFIGS=(
    bash_aliases
    bash_history
    fzf_bash_history
    fzf_catppuccin_theme
    screensaver
    zoxide
)

# Join the array into a space-separated string
_DOTFILES_PACKAGES_TO_INSTALL="${PACKAGES[*]}"
_DOTFILES_SCRIPTS_TO_INSTALL="${SCRIPTS[*]}"
_DOTFILES_CONFIGS_TO_INSTALL="${CONFIGS[*]}"
