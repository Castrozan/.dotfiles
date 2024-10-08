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
# Inicia a variável vazia
_DOTFILES_PACKAGES_TO_INSTALL=""
# Adiciona os pacotes à variável, linha por linha
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} bash_completion"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} cbonsai"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} fzf"
#_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} kitty"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} lazygit"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} neofetch"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} neovim"
#_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} nix"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} nodejs"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} npm"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} nvm"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} obsidian"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} pipes"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} tmux"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} vim"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} yazi"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} zoxide"
_DOTFILES_PACKAGES_TO_INSTALL="${_DOTFILES_PACKAGES_TO_INSTALL} zsh"

# Configs
# These are the configurations that are available
# Remove the ones that you don't want
#   Some of these are already sourced in my shell configs-
#   so to remove, comment out on the shell rc file
_DOTFILES_CONFIGS_TO_INSTALL=""
# Adicione itens à variável, comentando/descomentando conforme necessário
_DOTFILES_CONFIGS_TO_INSTALL="${_DOTFILES_CONFIGS_TO_INSTALL} bash_aliases"
_DOTFILES_CONFIGS_TO_INSTALL="${_DOTFILES_CONFIGS_TO_INSTALL} bash_history"
_DOTFILES_CONFIGS_TO_INSTALL="${_DOTFILES_CONFIGS_TO_INSTALL} fzf_bash_history"
_DOTFILES_CONFIGS_TO_INSTALL="${_DOTFILES_CONFIGS_TO_INSTALL} fzf_catppuccin_theme"
_DOTFILES_CONFIGS_TO_INSTALL="${_DOTFILES_CONFIGS_TO_INSTALL} git_aliases"
_DOTFILES_CONFIGS_TO_INSTALL="${_DOTFILES_CONFIGS_TO_INSTALL} screensaver"
_DOTFILES_CONFIGS_TO_INSTALL="${_DOTFILES_CONFIGS_TO_INSTALL} zoxide"
