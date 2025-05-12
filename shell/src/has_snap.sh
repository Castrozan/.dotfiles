#!/usr/bin/env bash

# Check if snap is available
has_snap() {
    if command -v snap >/dev/null 2>&1; then
        return 0
    fi
    return 1
} 