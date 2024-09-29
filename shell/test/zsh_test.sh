#!/bin/bash

# Test if zsh is installed
zsh_test() {

    if ! zsh --version | head -n 1; then
        print "Zsh is not installed." "$RED"
        exit 1
    else
        print "Zsh is installed." "$GREEN"
    fi
}

ohmyzsh_test() {
    if [ ! -d "$HOME/.oh-my-zsh" ]; then
        print "Oh-my-zsh is not installed." "$RED"
    else
        print "Oh-my-zsh is installed." "$GREEN"
    fi
}

# Run the test
zsh_test
ohmyzsh_test
