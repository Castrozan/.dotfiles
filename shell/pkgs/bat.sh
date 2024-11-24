#!/usr/bin/env bash

. "./shell/src/should_install.sh"
. "./shell/src/is_installed.sh"
. "./shell/src/print.sh"
. "./shell/src/is_already_installed.sh"

# Check if bat is installed
if ! is_installed bat; then
    should_install bat

    mkdir -p ~/.local/bin
    ln -s /usr/bin/batcat ~/.local/bin/bat
else
    is_already_installed bat
fi
