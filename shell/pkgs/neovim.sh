#!/bin/bash

. "./shell/src/should_install.sh"

# Install some nvim dependencies needed for the custom config
install_nvim_dependencies() {
    should_install ripgrep
    should_install fd-find
}

# Install neovim
install_nvim() {
    curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim-linux64.tar.gz
    rm -rf /opt/nvim
    tar -C /opt -xzf nvim-linux64.tar.gz
    rm -rf nvim-linux64.tar.gz

    install_nvim_dependencies
}

# Check if neovim is installed
if nvim --version >/dev/null 2>&1; then
    print "Neovim already installed" "$YELLOW"
else
    install_nvim
fi
