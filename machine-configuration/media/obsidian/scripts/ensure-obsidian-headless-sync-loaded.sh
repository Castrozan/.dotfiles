#!/usr/bin/env bash

set -uo pipefail

LABEL="com.dotfiles.obsidian-headless-sync"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"
LAUNCHCTL="/bin/launchctl"

if [ ! -f "$PLIST" ]; then
	exit 0
fi

if "$LAUNCHCTL" print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
	exit 0
fi

echo "obsidian-headless-sync agent not loaded; reconciling into $DOMAIN"
"$LAUNCHCTL" bootout "$DOMAIN" "$PLIST" 2>/dev/null || true
"$LAUNCHCTL" enable "$DOMAIN/$LABEL" 2>/dev/null || true
"$LAUNCHCTL" bootstrap "$DOMAIN" "$PLIST" 2>/dev/null || true
"$LAUNCHCTL" kickstart "$DOMAIN/$LABEL" 2>/dev/null || true

exit 0
