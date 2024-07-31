#!/bin/bash

# Define the scripting directory
INSTALL_SCRIPT_DIR="/shell"

# ---- Customizable variables ----
# Define the default package manager
PKG_MGR="apt"

# Define the original home directory
ORIGINAL_HOME=$(getent passwd $(logname) | cut -d: -f6)

# Default shell location
SH=$ORIGINAL_HOME"/.bashrc"

# Dotfiles home directory
DOTFILES_HOME="$ORIGINAL_HOME/.dotfiles_ubuntu"
echo $DOTFILES_HOME
echo $ORIGINAL_HOME

# Stow clause
STOW_CLAUSE="stow --adopt ."
