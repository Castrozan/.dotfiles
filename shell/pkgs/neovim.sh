#!/bin/bash

install_nvim() {
    curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim-linux64.tar.gz
    rm -rf /opt/nvim
    tar -C /opt -xzf nvim-linux64.tar.gz
    rm -rf nvim-linux64.tar.gz
}

# Check if neovim is installed
if ! nvim -v >/dev/null; then
    install_nvim
else
    print "Neovim already installed" "$YELLOW"
fi
