#!/usr/bin/env bash

. "./shell/src/run_elevated_clause.sh"

# Install pipes.sh
install_pipes() {
    git clone https://github.com/pipeseroni/pipes.sh "$HOME/repo/pipes.sh"
    run_elevated_clause "make -C $HOME/repo/pipes.sh install"
}

# Check if pipes.sh is installed
if [ -d "$HOME/repo/pipes.sh" ]; then
    print "Pipes.sh already installed" "$YELLOW"
else
    install_pipes
fi
