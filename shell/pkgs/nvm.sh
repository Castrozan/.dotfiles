#!/bin/sh

. "shell/src/install_with_temp_custom_script.sh"

# Check if nvm is installed
if nvm --version >/dev/null 2>&1; then
    print "Nvm already installed" "$YELLOW"
else
    install_with_temp_custom_script "https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh" "curl" "-L" "bash"
fi
