#!/bin/bash

# Test if fzf is installed
fzf_test() {

    print "TODO: fix test if fzf is installed." $RED
    # if brew info fzf &> /dev/null; then
    #     print "Fzf is installed." $GREEN
    # else
    #     print "Fzf is not installed." $RED
    #     exit 1
    # fi
}

# Test if fzf key bindings are working
fzf_keybinds_test() {

    print "TODO: fix test if fzf key bindings are working." $RED
    # if ! is_sourced "[ -f ~/.fzf.bash ] && source ~/.fzf.bash" ; then
    #     print "Fzf key bindings are not working." $RED
    #     exit 1
    # else
    #     print "Fzf key bindings are working." $GREEN
    # fi
}

# Run the test
fzf_test
fzf_keybinds_test