#!/bin/bash

# Define the scripting directory
INSTALL_SCRIPT_DIR="/shell"

# ---- Customizable variables ----
# Define the default package manager
PKG_MGR="apt"

# Default shell location
SH=$HOME"/.bashrc"

# Dotfiles home directory
DOTFILES_HOME="$HOME/.dotfiles_ubuntu"

# Directory with config scripts
CONFIG_SCRIPTS_DIR="$DOTFILES_HOME/shell/configs"

# Directory with install scripts
INSTALL_SCRIPTS_DIR="$DOTFILES_HOME/shell/pkgs"

# Stow clause
STOW_CLAUSE="stow --adopt ."

# Echo all variables
echo "PKG_MGR: $PKG_MGR"
echo "SH: $SH"
echo "DOTFILES_HOME: $DOTFILES_HOME"
echo "CONFIG_SCRIPTS_DIR: $CONFIG_SCRIPTS_DIR"
echo "INSTALL_SCRIPTS_DIR: $INSTALL_SCRIPTS_DIR"
echo "STOW_CLAUSE: $STOW_CLAUSE"