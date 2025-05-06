#!/usr/bin/env bash

# Check if the system is Ubuntu
is_ubuntu() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [ "$ID" = "ubuntu" ]; then
            return 0
        fi
    fi
    return 1
} 