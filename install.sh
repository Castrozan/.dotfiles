#!/bin/bash

# Tell that the script is sourcing src
echo "Sourcing helper files..."
for file in shell/src/*; do
    if [ -f "$file" ]; then
        . "$file" # Source the file
    fi
done

# Tell what is going to happen
print "# -------------- castrozan:dotfiles install script ---------------\n" "${MAGENTA}" "${BOLD}"

print "Some packages are required to run the install script.\n" "${YELLOW}" "${BOLD}"
if ask "Do you want to install them?"; then
    should_install curl
    should_install git
    use_brew
    use_stow
fi
print "\n"

# Ask if pkgs should be installed
if ask "Do you want to install pkgs?"; then
    iterate_install_scripts
fi
print "\n"

# Ask if configs should be sourced
if ask "Do you want to $SH to source files?"; then
    iterate_config_scripts
fi
print "\n"

# End of script
print "# ------------------------ End of script ------------------------\n" "${MAGENTA}" "${BOLD}"

# Final reminder to the user
print "To apply changes to your current shell session, run:\n" "${GREEN}"
print "source ~/.bashrc\n" "${GREEN}"

# Cutely tell goodbye
print "( ੭ ˘ ³˘)੭°｡⋆♡‧₊˚ bye!\n" "${CYAN}"