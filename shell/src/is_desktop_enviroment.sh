#!/bin/bash

# Function to check if the desktop enviroment is enabled
is_desktop_enviroment() {
    if [ -n "$DESKTOP_SESSION" ]; then
        return 0
    fi
    return 1
}
