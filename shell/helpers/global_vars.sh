#!/bin/bash

# Define the scripting directory
INSTALL_SCRIPT_DIR="/shell"

# ---- Customizable variables ----
# Define the default package manager
PKG_MGR="apt"

# Define default install clause
INSTALL_CLAUSE="sudo $PKG_MGR install"

# Default shell
SH="${HOME}/.bashrc"

# Dotfiles home directory
DOTFILES_HOME="$HOME/.dotfiles_ubuntu"
