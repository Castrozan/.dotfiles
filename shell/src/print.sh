#!/usr/bin/env bash

# Function to print a message with optional color and bold formatting
# $1: message (mandatory)
# $2: color (optional, e.g., $_RED, $_GREEN)
# $3: bold (optional, "true" for bold)
print() {
    local message=$1 color=${2:-$_RESET} bold=${3:-false}

    # Apply bold formatting if requested
    if [ "$bold" = "true" ] || [ "$bold" = "$_BOLD" ]; then
        printf "$color$bold%b$_RESET" "$message"
        echo
    else
        printf "$color%b$_RESET" "$message"
        echo
    fi
}
