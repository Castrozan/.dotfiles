#!/bin/bash

. "./shell/src/run_elevated_clause.sh"

# Install scdoc as it is a dependency of cbonsai man page
install_scdoc() {
    should_install scdoc
}

# Install ncurses as it is a dependency of cbonsai
install_ncurses() {
    apt install -y libncurses5-dev libncursesw5-dev
}

# Install cbonsai
install_cbonsai() {
    git clone https://gitlab.com/jallbrit/cbonsai "$HOME/repo/cbonsai"
    run_elevated_clause "make -C $HOME/repo/cbonsai install"
}

# Check if cbonsai is installed
if [ -d "$HOME/repo/cbonsai" ]; then
    print "Cbonsai already installed" "$YELLOW"
else
    install_ncurses
    install_scdoc
    install_cbonsai
fi
