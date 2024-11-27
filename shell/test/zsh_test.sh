#!/usr/bin/env bash

# Test if zsh is installed
zsh_test() {

    if ! zsh --version | head -n 1; then
        print "Zsh is not installed." "$_RED"
        exit 1
    else
        print "Zsh is installed." "$_GREEN"
    fi
}

ohmyzsh_test() {
    if [ ! -d "$HOME/.oh-my-zsh" ]; then
        print "Oh-my-zsh is not installed." "$_RED"
    else
        print "Oh-my-zsh is installed." "$_GREEN"
    fi
}

# Run the test
zsh_test
ohmyzsh_test
