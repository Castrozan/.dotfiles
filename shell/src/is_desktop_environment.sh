#!/usr/bin/env bash

# Function to check if the desktop environment is enabled
is_desktop_environment() {
    [ -n "$DESKTOP_SESSION" ]
}
