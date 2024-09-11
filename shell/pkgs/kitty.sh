#!/bin/sh

# Check if kitty is installed
if command -v kitty >/dev/null 2>&1; then
    print "Kitty already installed" "$YELLOW"
else
    install_with_custom_script_via_curl "https://sw.kovidgoyal.net/kitty/installer.sh"
fi
