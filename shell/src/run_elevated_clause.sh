#!/usr/bin/env bash

. "./shell/src/ask.sh"

# Function to run a command that may require sudo
# $1: command to be run
# $2: location to run the command (optional)
run_elevated_clause() {
    _clause="${1:- echo "No \$1 argument for run_elevated_clause()"}"
    _location="$2"

    # Attempt to run the command
    if ! $_clause; then

        # Check if the error is related to permission issues
        error_message=$($_clause 2>&1)

        # TODO: Check if error code is 126 or 100 (permission denied)
        if echo "$error_message" | grep -q "Permission denied"; then
            print "It looks like you need elevated permissions to run this script." "$_RED"

            if ask "Would you like to try running the command with sudo?"; then
                # shellcheck disable=SC2164
                [ -n "$2" ] && cd "$2"
                sudo "$_clause"
            else
                print "Skipping the command." "$_YELLOW"
            fi
        else
            print "An error occurred while trying to run the command:" "$_RED"
            print "$error_message" "$_RED"
        fi
    else
        print "Successfully ran the command." "$_GREEN"
    fi
}
