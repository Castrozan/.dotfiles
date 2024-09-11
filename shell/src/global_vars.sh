#!/bin/bash

# Define the scripting directory
_INSTALL_SCRIPT_DIR="/shell"

# ---- Customizable variables ----
# Define the default package manager
_PKG_MGR="apt"

# Default shell config location
_SH=$HOME"/.bashrc"

# Dotfiles home directory
_DOTFILES_HOME="$HOME/.dotfiles_ubuntu"

# Directory with config scripts
_CONFIG_SCRIPTS_DIR="shell/configs/"

# Directory with install scripts
_INSTALL_SCRIPTS_DIR="shell/pkgs/"

# Directory with src scripts
_SRC_SCRIPTS_DIR="shell/src"

# Directory with test scripts
_TEST_DIR="shell/test/"

# Stow clause
_STOW_CLAUSE="stow --adopt ."
