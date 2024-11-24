#!/usr/bin/env bash

. "./shell/src/should_install.sh"
. "./shell/src/install_with_temp_custom_script.sh"
. "./shell/src/run_elevated_clause.sh"

install_ohmyzsh() {
    if [ ! -d "$HOME/.oh-my-zsh" ]; then
        install_with_temp_custom_script "https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh" \
            "curl" \
            "-fsSL" \
            "sh" \
            "--unattended"
    fi
}

# Checks wheter the plugin is already installed and if not, installs it
# $1: git clone command
# $2: plugin path (e.g. $ZSH_CUSTOM/plugins/zsh-autosuggestions)
install_plugin() {
    if [ ! -d "$2" ]; then
        plugin_name=$(basename "$2")
        print "Installing plugin $plugin_name..." "$GREEN"
        run_elevated_clause "$1 $2"
    fi
}

install_zsh_plugins() {
    # zsh-autosuggestions plugin
    install_plugin "git clone https://github.com/zsh-users/zsh-autosuggestions.git" \
        "$ZSH_CUSTOM"/plugins/zsh-autosuggestions

    # zsh-syntax-highlighting plugin
    install_plugin "git clone https://github.com/zsh-users/zsh-syntax-highlighting.git" \
        "$ZSH_CUSTOM"/plugins/zsh-syntax-highlighting

    # zsh-fast-syntax-highlighting plugin
    install_plugin "git clone https://github.com/zdharma-continuum/fast-syntax-highlighting.git" \
        "$ZSH_CUSTOM"/plugins/fast-syntax-highlighting

    # zsh-autocomplete plugin
    install_plugin "git clone --depth 1 -- https://github.com/marlonrichert/zsh-autocomplete.git" \
        "$ZSH_CUSTOM"/plugins/zsh-autocomplete

    # zsh-fzf-history-search plugin
    install_plugin "git clone https://github.com/joshskidmore/zsh-fzf-history-search" \
        "$ZSH_CUSTOM"/plugins/zsh-fzf-history-search

    # Catppuccin theme for zsh-syntax-highlighting
    # Sourced on .zshrc
    curl "https://raw.githubusercontent.com/catppuccin/zsh-syntax-highlighting/refs/heads/main/themes/catppuccin_mocha-zsh-syntax-highlighting.zsh" \
        >"$ZSH_CUSTOM"/catppuccin_mocha-zsh-syntax-highlighting.zsh
}

# zsh home directory
# Seting it for installing scripts and plugins
if [ -z "$ZSH" ]; then
    ZSH="$HOME/.oh-my-zsh"
fi

# zsh custom directory for plugins and other customizations
# Seting it for installing scripts and plugins
if [ -z "$ZSH_CUSTOM" ]; then
    ZSH_CUSTOM=$ZSH/custom
fi

should_install zsh

# Check if zsh is installed to install oh-my-zsh and plugins
if zsh --version >/dev/null 2>&1; then
    install_ohmyzsh
    install_zsh_plugins
fi
