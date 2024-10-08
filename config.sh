#!/bin/bash

# This file is set for you to chose pkgs and configs that you want to install
# That way you can declarativly set up your system
# There are 2 types of configurations:
# _DOTFILES_PACKAGES_TO_INSTALL: These are packages that you want to install
# _DOTFILES_CONFIGS_TO_INSTALL: These are configurations that you want to set up
# Below are array like structures that you should modify to install-
# the packages and configs that you want
# Now it shows all packages and configs that are available

# Packages
# These are the packages that are available
# remove the ones that you don't want
_DOTFILES_PACKAGES_TO_INSTALL="\
    bash_completion cbonsai fzf kitty lazygit \
    neofetch neovim nix nodejs npm nvm obsidian \
    pipes tmux vim yazi zoxide zsh"

# Configs
# These are the configurations that are available
# Remove the ones that you don't want
#   Some of these are already sourced in my shell configs-
#   so to remove, comment out on the shell rc file
_DOTFILES_CONFIGS_TO_INSTALL="\
    bash_aliases bash_history fzf_bash_history \
    fzf_catppuccin_theme git_aliases screensaver \
    zoxide"
