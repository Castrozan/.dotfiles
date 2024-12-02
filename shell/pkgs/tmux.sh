#!/usr/bin/env bash

. "./shell/src/should_install.sh"

should_install tmux

# Check if plugins/tpm exists and install it
if [ -d "$HOME/.config/tmux/plugins/tpm" ]; then
    print "Tmux plugin manager already installed" "$_YELLOW"
else
    git clone https://github.com/tmux-plugins/tpm "$HOME/.config/tmux/plugins/tpm"
fi
