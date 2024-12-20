#!/usr/bin/env bash

. "./shell/src/ask.sh"
. "./shell/src/print.sh"
. "./shell/src/should_install.sh"
. "./shell/src/install_scripts.sh"
. "./shell/src/install_pkgs.sh"
. "./shell/src/install_configs.sh"
. "./shell/src/use_tzdata.sh"
. "./shell/src/use_brew.sh"
. "./shell/src/use_stow.sh"
. "./shell/src/use_flatpak.sh"

# Tell that the script is sourcing src
# TODO: remove it after refactoring to import src files manually
echo "Sourcing helper files..."
for file in shell/src/*; do
    if [ -f "$file" ]; then
        # shellcheck disable=SC1090
        . "$file" # Source the file
    fi
done

# TODO: check if any of the params are -d not only the first one
# Check if -d flag is passed and source declarative install script
if [ "$1" = "-d" ]; then
    . "./declarative.sh"
fi

# Tell what is going to happen
print "# -------------- castrozan:dotfiles install script ---------------\n" "$_MAGENTA" "$_BOLD"

print "Some packages are required to run the install script.\n" "$_YELLOW" "$_BOLD"
if ask "Do you want to install them?"; then
    should_install build-essential
    should_install curl
    should_install git
    # use_tzdata
    # use_flatpak
    # use_brew
    # use_stow
fi
print "\n"

# Ask if pkgs should be installed
if ask "Do you want to install pkgs?"; then
    install_pkgs
fi
print "\n"

# Ask if scripts should be installed
if ask "Do you want to install scripts?"; then
    install_scripts
fi
print "\n"

# Ask if configs should be sourced
if ask "Do you want to $_SH to source files?"; then
    install_configs
fi
print "\n"

# End of script
print "# ------------------------ End of script ------------------------\n" "$_MAGENTA" "$_BOLD"

# Final reminder to the user
print "To apply changes to your current shell session, run:\n" "$_GREEN" "$_BOLD"
print "git reset --hard origin/main\n" "$_GREEN" "$_BOLD"
print "source ~/.bashrc\n" "$_GREEN" "$_BOLD"

# Cutely tell goodbye
print "( ੭ ˘ ³˘)੭°｡⋆♡‧₊˚ bye!\n" "$_CYAN"
