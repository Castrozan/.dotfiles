#!/bin/sh

# Check if kitty is installed
if command -v kitty >/dev/null 2>&1; then
    print "Kitty already installed" "$YELLOW"
else
    curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin
fi
