#!/bin/bash

# Define the scripting directory
INSTALL_SCRIPT_DIR="/shell"

# ---- Customizable variables ----
# Define the default package manager
PKG_MGR="apt"

# Default shell config location
SH=$HOME"/.bashrc"

# Dotfiles home directory
DOTFILES_HOME="$HOME/.dotfiles_ubuntu"

# Directory with config scripts
CONFIG_SCRIPTS_DIR="shell/configs/"

# Directory with install scripts
INSTALL_SCRIPTS_DIR="shell/pkgs/"

# Directory with test scripts
TEST_DIR="shell/test/"

# Stow clause
STOW_CLAUSE="stow --adopt ."