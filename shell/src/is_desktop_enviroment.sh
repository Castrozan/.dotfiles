#!/bin/bash

# Function to check if the desktop enviroment is installed
is_desktop_enviroment() {
    if echo "$DESKTOP_SESSION"; then
        return 0
    fi

    return 1
}
