#!/usr/bin/env bash

. "./shell/src/should_install.sh"
. "./shell/src/print.sh"

should_install zoxide
print "Make sure to install fzf for optimal zoxide functionality." "$_YELLOW"
