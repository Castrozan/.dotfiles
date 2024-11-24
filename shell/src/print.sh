#!/usr/bin/env bash

# Function to print a message with optional color and bold formatting
# $1: message (mandatory)
# $2: color (optional, e.g., $RED, $GREEN)
# $3: bold (optional, "true" for bold)
print() {
    local message=$1 color=${2:-$RESET} bold=${3:-false}

    # Apply bold formatting if requested
    if [ "$bold" = "true" ] || [ "$bold" = "$BOLD" ]; then
        printf "$color$bold%b$RESET" "$message"
        echo
    else
        printf "$color%b$RESET" "$message"
        echo
    fi
}
