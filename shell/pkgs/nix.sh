#!/usr/bin/env bash

. "./shell/src/install_with_temp_custom_script.sh"
. "./shell/src/install_with_sh.sh"
. "./shell/src/run_elevated_clause.sh"

install_nix() {
    # Check if nix is installed
    if nix --version >/dev/null 2>&1; then
        print "Nix already installed" "$_YELLOW"
    else
        # install_with_temp_custom_script "https://nixos.org/nix/install" "curl" \
        #     "-L" \
        #     "sh" \
        #     "--no-daemon --yes --no-channel-add"
        install_with_sh "sh" "curl" "-L" "https://nixos.org/nix/install" "--no-daemon --yes --no-channel-add"
        #   . /home/ciuser/.nix-profile/etc/profile.d/nix.sh
    fi
}

# Install nix
install_nix
