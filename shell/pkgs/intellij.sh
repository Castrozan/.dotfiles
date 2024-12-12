#!/usr/bin/env bash

. "./shell/src/should_install.sh"
. "./shell/src/run_elevated_clause.sh"

# Install Intellij
install_intellij() {
    curl -LO https://download.jetbrains.com/idea/ideaIU-2024.3.1.tar.gz
    run_elevated_clause "rm -rf /opt/idea-IU-*" "Remove old Intellij installations"
    run_elevated_clause "tar -xzf ideaIU-*.tar.gz -C /opt" "Extract Intellij"
    rm -rf ideaIU-*.tar.gz
}

# Check if Intellij is installed
# shellcheck disable=SC2211
if /opt/idea-IU-*/bin/idea --version >/dev/null 2>&1; then
    print "Intellij already installed" "$_YELLOW"
else
    install_intellij
fi
