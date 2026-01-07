#!/usr/bin/env bash

# List of commands to run in screensaver (in order)
# First command gets full pane, subsequent commands split horizontally
# shellcheck disable=SC2034
SCREENSAVER_COMMANDS=(
    'cbonsai -l -i -b 1 -c mWmW,wMwM,mMw -M 2 --life 35 -f 60'
    'cmatrix'
    'install-nothing --all --exclude deno'
)

