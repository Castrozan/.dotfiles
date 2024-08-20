#!/bin/bash

# Function to print a message
# $1: message
# $2: color (optional)
# $3: bold (optional)
print() {
    local RESET="\033[0m"
    local message=$1
    local color=$2
    local bold=$3

    echo "${color}${bold}${message}${RESET}"
}