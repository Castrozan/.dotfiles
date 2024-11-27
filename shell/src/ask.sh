#!/usr/bin/env bash

# TODO: enable color and bold support
# Ask Y/n question with color
# $1: prompt
ask() {
    local prompt="$1"
    local resp

    # Use printf to display the prompt with colors
    printf "$_CYAN%b$_RESET (Y/n): " "$prompt"

    # Read the user input
    read -r resp

    if [ -z "$resp" ]; then
        # empty is Yes
        response_lc="y"
    else
        # case insensitive
        response_lc=$(echo "$resp" | tr '[:upper:]' '[:lower:]')
    fi

    [ "$response_lc" = "y" ]
}
