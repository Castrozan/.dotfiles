#!/usr/bin/env bash

# Screensaver tmux session layout:
#
# ┌──────────────────────┬───────────┐
# │                      │  cmatrix  │
# │    openclaw-mesh     │  (pane 2) │
# │      (pane 1)        ├───────────┤
# │       70%            │ bad-apple │
# │                      │  (pane 3) │
# └──────────────────────┴───────────┘
#
# Pane 1 (left, 70% width):        openclaw-mesh
# Pane 2 (top-right, 30% width):   cmatrix
# Pane 3 (bottom-right, 50% height of right column): bad-apple
#
# shellcheck disable=SC2034
SCREENSAVER_COMMANDS=(
    'openclaw-mesh'
    'cmatrix'
    'sleep 3; bad-apple'
)
