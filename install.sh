#!/bin/bash

# Tell that the script is sourcing helper files
echo "Sourcing helper files..."
for file in shell/helpers/*; do
    if [ -f "$file" ]; then
        . "$file" # Source the file
    fi
done

# Ask if stow should be used
echo "${YELLOW}${BOLD}Some packages are required to run the install script.${RESET}"
if ask "Do you want to install them?"; then
    should_install curl
fi
echo ""

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

# Ask if stow should be used
echo "${YELLOW}${BOLD}Stow is required to create symlinks.${RESET}"
if ask "Do you want to use stow?"; then
    use_stow
fi
echo ""

# Ask if pkgs should be installed
if ask "Do you want to install pkgs?"; then
    echo "$DOTFILES_HOME$INSTALL_SCRIPT_DIR/pkgs/*"
    iterate_install_scripts "$DOTFILES_HOME$INSTALL_SCRIPT_DIR/pkgs/*"
fi
echo ""

# Ask if configs should be sourced
if ask "Do you want to $SH to source files?"; then
    iterate_config_scripts "$DOTFILES_HOME$INSTALL_SCRIPT_DIR/configs/*"
fi
echo ""

# End of script
echo "${MAGENTA}${BOLD}# ------------------------ End of script ------------------------${RESET}"
echo ""

# Final reminder to the user
echo "${GREEN}To apply changes to your current shell session, run:${RESET}"
echo "${GREEN}source ~/.bashrc${RESET}"
echo ""

# Cutely tell goodbye
printf "${CYAN}( ੭ ˘ ³˘)੭°｡⋆♡‧₊˚ bye!${RESET}\n"
echo ""
echo ""
