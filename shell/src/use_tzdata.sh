#!/bin/bash

. "./shell/src/is_installed.sh"

# tzdata is a dependency of some packages
# tzdata is a package that allows you to set the timezone of the system
# without user interaction. This is useful when you are installing
# packages that depend on the timezone being set.
use_tzdata() {
    export DEBIAN_FRONTEND=noninteractive

    if ! is_installed tzdata; then
        ln -fs /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime
        apt-get install -y tzdata
        dpkg-reconfigure --frontend noninteractive tzdata
    fi
}
