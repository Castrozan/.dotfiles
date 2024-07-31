#!/bin/bash

# Function to check if a package is installed
# $1: package name
is_installed() {
    dpkg -l | grep -q $1
    echo "checking if $1 is installed..."
}