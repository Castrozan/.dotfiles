#!/bin/bash

. "./shell/src/should_install.sh"

# Function to install flatpack
use_flatpak() {
    should_install flatpak
}
