#!/bin/bash
# Default directories for the shell

# Create repo directory if it doesn't exist
if [ ! -d "$HOME/repo" ]; then
    mkdir -p "$HOME/repo"
fi

# Create satc directory if it doesn't exist
if [ ! -d "$HOME/repo/satc" ]; then
    mkdir -p "$HOME/repo/satc"
fi

# Create fonts directory if it doesn't exist
if [ ! -d "$HOME/.local/share/fonts" ]; then
    mkdir -p "$HOME/.local/share/fonts"
fi
