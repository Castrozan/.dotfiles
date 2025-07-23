#!/usr/bin/env bash

# Function for cbonsai
bonsai() {
    cbonsai "$@"
}

# Function for pipes.sh
pipes() {
    pipes.sh "$@"
}

# Function for pipes as screensaver
pipes_screensaver() {
    pipes
}

# Function for cbonsai as screensaver
bonsai_screensaver() {
    bonsai -l -i -b 1 -c mWmW,wMwM,mMw -M 2 --life 35
}
