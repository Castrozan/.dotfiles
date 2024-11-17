#!/bin/bash

# This file is set for you to chose pkgs and configs that you want to install
# That way you can declarativly set up your system
# There are 2 types of configurations:
# _DOTFILES_PACKAGES_TO_INSTALL: These are packages that you want to install
# _DOTFILES_CONFIGS_TO_INSTALL: These are configurations that you want to set up
# Below are array like structures that you should modify to install-
# the packages and configs that you want
# Now it shows all packages and configs that are available
# It is up to you to comment the ones that you don't want

# Packages
# These are the packages that are available
# They are set this way to make it easier to comment out the ones you don't want
_PKG_SEL=""
_PKG_SEL="$_PKG_SEL bash_completion"
_PKG_SEL="$_PKG_SEL btop"
_PKG_SEL="$_PKG_SEL cbonsai"
_PKG_SEL="$_PKG_SEL fzf"
# _PKG_SEL="$_PKG_SEL kitty"
_PKG_SEL="$_PKG_SEL lazygit"
_PKG_SEL="$_PKG_SEL neofetch"
_PKG_SEL="$_PKG_SEL neovim"
# _PKG_SEL="$_PKG_SEL nix"
_PKG_SEL="$_PKG_SEL nodejs"
_PKG_SEL="$_PKG_SEL npm"
_PKG_SEL="$_PKG_SEL nvm"
_PKG_SEL="$_PKG_SEL obsidian"
_PKG_SEL="$_PKG_SEL fira_code"
_PKG_SEL="$_PKG_SEL pipes"
_PKG_SEL="$_PKG_SEL tmux"
_PKG_SEL="$_PKG_SEL vim"
_PKG_SEL="$_PKG_SEL yazi"
_PKG_SEL="$_PKG_SEL zoxide"
_PKG_SEL="$_PKG_SEL zsh"
_DOTFILES_PACKAGES_TO_INSTALL="$_PKG_SEL"

# Configs
# These are the configurations that are available
# Remove the ones that you don't want
#   Some of these are already sourced in my shell configs-
#   so to remove, comment out on the shell rc file
# They are set this way to make it easier to comment out the ones you don't want
_CONFIG_SEL=""
_CONFIG_SEL="$_CONFIG_SEL bash_aliases"
_CONFIG_SEL="$_CONFIG_SEL bash_history"
_CONFIG_SEL="$_CONFIG_SEL fzf_bash_history"
_CONFIG_SEL="$_CONFIG_SEL fzf_catppuccin_theme"
_CONFIG_SEL="$_CONFIG_SEL git_aliases"
_CONFIG_SEL="$_CONFIG_SEL screensaver"
_CONFIG_SEL="$_CONFIG_SEL zoxide"
_DOTFILES_CONFIGS_TO_INSTALL="$_CONFIG_SEL"
