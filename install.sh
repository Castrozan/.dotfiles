#!/bin/bash

# Define colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

DOTFILES_HOME="$HOME/.dotfiles_ubuntu"
INSTALL_SCRIPT_DIR="/shell"

# Check internet connection
internet_on() {
    ping -c 1 google.com
}

# Ask Y/n question
ask() {
    read -p "$1 (Y/n): " resp
    if [ -z "$resp" ]; then
        # empty is Yes
        response_lc="y" 
    else
        # case insensitive
        response_lc=$(echo "$resp" | tr '[:upper:]' '[:lower:]') 
    fi

    [ "$response_lc" = "y" ]
}

# Default shell is bash
SH="${HOME}/.bashrc"

# Tell the user what is going to happen
echo "${MAGENTA}${BOLD}# -------------- castrozan:dotfiles install script ---------------${RESET}"
echo ""

# Tell that internet connection is required
echo "${YELLOW}${BOLD}Internet connection is required.${RESET}"
if ! internet_on; then
    echo "${RED}No internet connection.${RESET}"
    exit 1
fi
echo "${GREEN}Internet connection established.${RESET}"
echo ""

# Tell that Stow is required to create symlinks 
# and ask if it should be installed
echo "${CYAN}Stow is required to create symlinks.${RESET}"
if ask "Do you want to install stow?"; then
    #apt install stow
    echo "${GREEN}Stow installed.${RESET}"
    echo ""
fi

# Ask which apps should be installed
echo "${CYAN}Do you want to install:${RESET}"
for file in $DOTFILES_HOME$INSTALL_SCRIPT_DIR/pkgs/*; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        if ask "${filename}?"; then
            #echo "source $(realpath "$file")" >> "$SH"
            echo "${GREEN}${filename} sourced${RESET}"
        fi
    fi
done
echo ""

# Ask which files should be sourced
echo "${CYAN}Do you want $SH to source:${RESET}"
for file in $DOTFILES_HOME$INSTALL_SCRIPT_DIR/config/*; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        if ask "${filename}?"; then
            #echo "source $(realpath "$file")" >> "$SH"
            echo "${GREEN}${filename} sourced${RESET}"
        fi
    fi
done
echo ""

# Ask if the shell should be reloaded
if ask "Do you want to reload the shell?"; then
    #source $SH
    echo "${GREEN}Shell reloaded.${RESET}"
    echo ""
fi

echo "${MAGENTA}${BOLD}# -------------- End of script ---------------${RESET}"
