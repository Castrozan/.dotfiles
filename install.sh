#!/bin/sh

. "./shell/src/ask.sh"
. "./shell/src/print.sh"
. "./shell/src/should_install.sh"
. "./shell/src/iterate_install_scripts.sh"
. "./shell/src/iterate_config_scripts.sh"
. "./shell/src/use_brew.sh"
. "./shell/src/use_stow.sh"

# Tell that the script is sourcing src
# TODO: remove it after refactoring to import src files manually
echo "Sourcing helper files..."
for file in shell/src/*; do
    if [ -f "$file" ]; then
        # shellcheck disable=SC1090
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
if ask "Do you want to $_SH to source files?"; then
    iterate_config_scripts
fi
print "\n"

# End of script
print "# ------------------------ End of script ------------------------\n" "${MAGENTA}" "${BOLD}"

# Final reminder to the user
print "To apply changes to your current shell session, run:\n" "${GREEN}" "${BOLD}"
print "git reset --hard origin/main\n" "${GREEN}" "${BOLD}"
print "source ~/.bashrc\n" "${GREEN}" "${BOLD}"

# Cutely tell goodbye
print "( ੭ ˘ ³˘)੭°｡⋆♡‧₊˚ bye!\n" "${CYAN}"
