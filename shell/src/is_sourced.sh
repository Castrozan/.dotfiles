#!/usr/bin/env bash

# Function to check if a file is already sourced in .bashrc
# $1: file to check
is_sourced() {
    _file="$1"
    grep -q ". $_file" "$_SH"
}
