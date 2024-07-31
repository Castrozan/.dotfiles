#!/bin/bash

# Tell that the script is sourcing helper files
echo "Sourcing helper files..."
for file in shell/helpers/*; do
    if [ -f "$file" ]; then
        . "$file" # Source the file
    fi
done

# Tell what is going to happen
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
echo "${YELLOW}Stow is required to create symlinks.${RESET}"
should_install stow
echo ""

# Ask if pkgs should be installed
if ask "Do you want to install pkgs?"; then
    iterate_install_scripts "$DOTFILES_HOME$INSTALL_SCRIPT_DIR/pkgs/*"
fi
echo ""

# Ask if configs should be sourced
if ask "Do you want to $SH to source files?"; then
    iterate_config_scripts "$DOTFILES_HOME$INSTALL_SCRIPT_DIR/configs/*"
fi
echo ""

# Ask if the shell should be reloaded
if ask "Do you want to reload the shell?"; then
    #source $SH
    echo "${GREEN}Shell reloaded.${RESET}"
fi
echo ""

echo "${MAGENTA}${BOLD}# -------------- End of script ---------------${RESET}"
