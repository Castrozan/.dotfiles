#!/usr/bin/env bash

# List of commands to run in screensaver (in order)
# First command gets 80% left pane, remaining split vertically on the right 20%
# shellcheck disable=SC2034
SCREENSAVER_COMMANDS=(
    'openclaw-mesh'
    'cmatrix'
    'sleep 3; bad-apple'
)
