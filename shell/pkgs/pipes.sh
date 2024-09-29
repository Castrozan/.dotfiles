#!/bin/bash

. "./shell/src/run_elevated_clause.sh"

# Install pipes.sh
pipes() {
    git clone https://github.com/pipeseroni/pipes.sh "$HOME/repo/pipes.sh"
    cd "$HOME/repo/pipes.sh" || exit
    run_elevated_clause "make install"
}

# Check if pipes.sh is installed
if [ -d "$HOME/repo/pipes.sh" ]; then
    print "Pipes.sh already installed" "$YELLOW"
else
    pipes
fi
