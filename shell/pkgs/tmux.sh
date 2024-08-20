#!/bin/bash

should_install tmux

# Check if plugins/tpm exists and install it
if [ ! -d ~/.config/tmux/plugins/tpm ]; then
    git clone https://github.com/tmux-plugins/tpm ~/.config/tmux/plugins/tpm
else 
    print "Tmux plugin manager already installed" $YELLOW
fi
