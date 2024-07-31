#!/bin/bash

# Define the scripting directory
INSTALL_SCRIPT_DIR="/shell"

# ---- Customizable variables ----
# Define the default package manager
PKG_MGR="apt"

# Default shell location
SH="${HOME}/.bashrc"

# Dotfiles home directory
DOTFILES_HOME="$HOME/.dotfiles_ubuntu"

# Stow clause
STOW_CLAUSE="stow --adopt ."

# Default install directory
# install_pkg() function will use this as the default install directory
DEFAULT_INSTALL_DIR="$HOME"