#!/usr/bin/env bash

. "./shell/src/should_install.sh"
. "./shell/src/is_desktop_environment.sh"

if is_desktop_environment; then
    should_install flameshot
fi
