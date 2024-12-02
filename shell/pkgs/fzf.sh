#!/usr/bin/env bash

. "./shell/src/print.sh"
. "./shell/src/should_install.sh"

should_install fzf brew
print "TODO: fix fzf install script. it works but returns error." "$_RED"
