#!/usr/bin/env bash
# TODO: this should not be done in the shell

if [ ! -d "$HOME/repo" ]; then
    mkdir -p "$HOME/repo"
fi

if [ ! -d "$HOME/repo/satc" ]; then
    mkdir -p "$HOME/repo/satc"
fi

if [ ! -d "$HOME/.local/share/fonts" ]; then
    mkdir -p "$HOME/.local/share/fonts"
fi
