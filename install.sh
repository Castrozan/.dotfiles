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

echo "${YELLOW}${BOLD}Some packages are required to run the install script.${RESET}"
if ask "Do you want to install them?"; then
    should_install curl

    # Ask if stow should be used
    echo "${YELLOW}${BOLD}Stow is required to create symlinks.${RESET}"
    if ask "Do you want to use stow?"; then
        use_stow
    fi
fi
echo ""

# Ask if pkgs should be installed
if ask "Do you want to install pkgs?"; then
    iterate_install_scripts
fi
echo ""

# Ask if configs should be sourced
if ask "Do you want to $SH to source files?"; then
    iterate_config_scripts
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
