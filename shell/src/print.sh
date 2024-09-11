#!/bin/sh

# Function to print a message
# $1: message
# $2: color (optional)
# $3: bold (optional)
print() {
    _RESET="\033[0m"
    _message=$1
    _color=$2
    _bold=$3

    echo "${_color}${_bold}${_message}${_RESET}"
}
