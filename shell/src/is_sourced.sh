#!/bin/bash

# Function to check if a file is already sourced in .bashrc
# $1: file to check
is_sourced() {
    local file="$1"
    grep -q ". $file" "$SH"
}