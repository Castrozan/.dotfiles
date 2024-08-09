#!/bin/bash

# tzdata is a vim dependency
# tzdata is a package that allows you to set the timezone of the system
# without user interaction. This is useful when you are installing
# packages that depend on the timezone being set.
install_tzdata() {
    export DEBIAN_FRONTEND=noninteractive

    ln -fs /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime
    apt-get install -y tzdata
    dpkg-reconfigure --frontend noninteractive tzdata
}

install_tzdata
should_install vim
