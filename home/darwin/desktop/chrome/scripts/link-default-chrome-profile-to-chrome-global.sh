#!/usr/bin/env bash
set -euo pipefail

chromeGlobalUserDataDirectory="$1"
defaultChromeUserDataDirectory="$2"
browserDisplayProcessName="$3"

if /usr/bin/pgrep -x "$browserDisplayProcessName" >/dev/null 2>&1; then
	echo "INFO: $browserDisplayProcessName is running; default-profile symlink deferred, a later rebuild retries." >&2
	exit 0
fi

mkdir -p "$chromeGlobalUserDataDirectory"

if [ -L "$defaultChromeUserDataDirectory" ]; then
	if [ "$(readlink "$defaultChromeUserDataDirectory")" = "$chromeGlobalUserDataDirectory" ]; then
		exit 0
	fi
	rm -f "$defaultChromeUserDataDirectory"
elif [ -e "$defaultChromeUserDataDirectory" ]; then
	backupDirectory="$defaultChromeUserDataDirectory.pre-chrome-global-symlink-backup"
	if [ -e "$backupDirectory" ]; then
		rm -rf "$defaultChromeUserDataDirectory"
	else
		mv "$defaultChromeUserDataDirectory" "$backupDirectory"
	fi
fi

mkdir -p "$(dirname "$defaultChromeUserDataDirectory")"
ln -s "$chromeGlobalUserDataDirectory" "$defaultChromeUserDataDirectory"
echo "INFO: linked the default Chrome profile path to $chromeGlobalUserDataDirectory so every launch path shares one profile"
