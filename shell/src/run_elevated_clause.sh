#!/usr/bin/env bash

. "./shell/src/ask.sh"
. "./shell/src/print.sh"

# Function to run a command that may require sudo
# $1: command to be run
# $2: description of the command
run_elevated_clause() {
    _clause="$1"
    _description="$2"

    print "It looks like you need elevated permissions to run '$_clause'" "$_RED"
    print "Description: $_description" "$_YELLOW"

    if ask "Would you like to try running the command with sudo?"; then
        # shellcheck disable=SC2086

        if sudo -u root $_clause; then
            print "Command ran successfully." "$_GREEN"
        else
            print "Command failed." "$_RED"
        fi
    else
        print "Skipping the command." "$_YELLOW"
    fi
}
