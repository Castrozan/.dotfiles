#!/usr/bin/env bash

# Functions for cursor - allows parameters and runs detached
cursor() {
    command cursor "$@" > /dev/null 2>&1 &
}

# Function for cu - defaults to current directory if no params, otherwise passes all params
cu() {
    if [ $# -eq 0 ]; then
        cursor .
    else
        cursor "$@"
    fi
}