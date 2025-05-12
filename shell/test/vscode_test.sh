#!/usr/bin/env bash

. "./shell/src/print.sh"

# Test if VS Code is installed
vscode_test() {
    if ! code --version | head -n 1; then
        print "VS Code is not installed." "$_RED"
        exit 1
    else
        print "VS Code is installed." "$_GREEN"
    fi
}

# Run the test
vscode_test 