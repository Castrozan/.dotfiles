#!/bin/bash

# Test if git aliases was sourced
git_aliases_test() {
    # TODO: fix test that the file was sourced
    # not that the alias is working
    #test_gs
    print "TODO: fix git aliases tests" $RED
    print "Skip Test git aliases" $RED
}

# Test if gs = git status was sourced
test_gs() {
    echo "Test gs"
    if ! gs; then
        print "gs was not sourced." $RED
        exit 1
    else
        print "gs was sourced." $GREEN
    fi
}

# Run the test
git_aliases_test