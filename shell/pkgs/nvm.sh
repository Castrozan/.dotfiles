#!/usr/bin/env bash

. "shell/src/install_with_temp_custom_script.sh"

# Check if nvm is installed
if nvm --version; then
    print "Nvm already installed" "$_YELLOW"

    _source_config_by_name "shell/configs/nvm.sh"
else
    install_with_temp_custom_script "https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh" "curl" "-L" "bash"
fi
