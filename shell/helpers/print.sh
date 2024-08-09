#!/bin/bash

# Function to print a message
# $1: message
# $2: color (optional)
print() {
    local RESET="\033[0m"
    local message=$1
    local color=$2

    echo "${color}${message}${RESET}"
}