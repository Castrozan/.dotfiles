#!/bin/bash

. "./shell/src/should_install.sh"
. "./shell/src/install_with_temp_custom_script.sh"

install_ohmyzsh() {
    if [ ! -d "$HOME/.oh-my-zsh" ]; then
        install_with_temp_custom_script "https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh" \
            "curl" \
            "-fsSL" \
            "sh" \
            "--unattended"
    fi
}

should_install zsh

# Check if zsh is installed to install oh-my-zsh
if ! zsh --version >/dev/null 2>&1; then
    install_ohmyzsh
fi
