#!/bin/bash

install_nvim() {
    curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim-linux64.tar.gz
    rm -rf /opt/nvim
    tar -C /opt -xzf nvim-linux64.tar.gz
    rm -rf nvim-linux64.tar.gz
}

# Check if neovim is installed
if command -v nvim >/dev/null 2>&1; then
    print "Neovim already installed" "$YELLOW"
else
    install_nvim
fi
