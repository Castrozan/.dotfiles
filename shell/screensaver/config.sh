#!/usr/bin/env bash

# List of commands to run in screensaver (in order)
# First command gets full pane, subsequent commands split horizontally
# Commands include all arguments - no wrapper functions needed
# shellcheck disable=SC2034
SCREENSAVER_COMMANDS=(
    'cbonsai -l -i -b 1 -c mWmW,wMwM,mMw -M 2 --life 35 -o "🎄,⭐,🎁,🔔" -f 60'
    'install-nothing --all --exclude xorg'
    'cmatrix -U "🎄,⭐,🎁,🔔" -F 10'
)

