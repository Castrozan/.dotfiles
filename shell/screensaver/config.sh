#!/usr/bin/env bash

# List of commands to run in screensaver (in order)
# First command gets full pane, subsequent commands split horizontally
# shellcheck disable=SC2034
SCREENSAVER_COMMANDS=(
    'install-nothing --all --exclude deno'
    'cmatrix'
    'bad-apple'
)

