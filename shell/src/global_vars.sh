#!/usr/bin/env bash

# ---- Customizable variables ----
# Default package manager
_PKG_MGR="apt"

# Default shell config location
_SH=$HOME"/.bashrc"

# Dotfiles home directory
_DOTFILES_HOME="$HOME/.dotfiles"

# Dotfiles dir name
_DOTFILES_DIR=".dotfiles"

# Directory with config scripts
_CONFIGS_DIR="shell/configs"

# Directory with install scripts
_PKGS_DIR="shell/pkgs"

# Directory with src scripts
_SRC_DIR="shell/src"

# Directory with test scripts
_TEST_DIR="shell/test"

# Stow clause
_STOW_CLAUSE="stow --no-folding --adopt ."
