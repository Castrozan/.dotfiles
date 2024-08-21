#!/bin/bash

should_install fzf brew

# Check if fzf is installed to install keybinds
if is_installed fzf brew; then
    print "Keybinds already installed" $YELLOW
else
    # Install useful key bindings and fuzzy completion piping yes to the install script and without showing output on the terminal
    yes | $(brew --prefix)/opt/fzf/install
fi