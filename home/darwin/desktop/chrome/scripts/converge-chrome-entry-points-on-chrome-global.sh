#!/usr/bin/env bash
set -euo pipefail

chromeGlobalUserDataDirectory="$1"
defaultChromeUserDataDirectory="$2"
browserDisplayProcessName="$3"
dutiBinary="$4"
chromeBundleIdentifier="$5"
retiredLinkHandlerApplicationPath="$6"

if /usr/bin/pgrep -x "$browserDisplayProcessName" >/dev/null 2>&1; then
	echo "INFO: $browserDisplayProcessName is running; chrome-global entry-point convergence deferred, a later rebuild retries." >&2
	exit 0
fi

mkdir -p "$chromeGlobalUserDataDirectory"

if [ -L "$defaultChromeUserDataDirectory" ]; then
	if [ "$(readlink "$defaultChromeUserDataDirectory")" != "$chromeGlobalUserDataDirectory" ]; then
		rm -f "$defaultChromeUserDataDirectory"
		ln -s "$chromeGlobalUserDataDirectory" "$defaultChromeUserDataDirectory"
	fi
elif [ -e "$defaultChromeUserDataDirectory" ]; then
	backupDirectory="$defaultChromeUserDataDirectory.pre-chrome-global-symlink-backup"
	if [ -e "$backupDirectory" ]; then
		rm -rf "$defaultChromeUserDataDirectory"
	else
		mv "$defaultChromeUserDataDirectory" "$backupDirectory"
	fi
	mkdir -p "$(dirname "$defaultChromeUserDataDirectory")"
	ln -s "$chromeGlobalUserDataDirectory" "$defaultChromeUserDataDirectory"
else
	mkdir -p "$(dirname "$defaultChromeUserDataDirectory")"
	ln -s "$chromeGlobalUserDataDirectory" "$defaultChromeUserDataDirectory"
fi

for urlScheme in http https; do
	"$dutiBinary" -s "$chromeBundleIdentifier" "$urlScheme" || echo "WARN: could not set $chromeBundleIdentifier as the default $urlScheme handler." >&2
done

if [ -e "$retiredLinkHandlerApplicationPath" ]; then
	rm -rf "$retiredLinkHandlerApplicationPath"
fi

echo "INFO: converged Chrome entry points on $chromeGlobalUserDataDirectory: default profile symlinked, plain Chrome set as default browser, retired link-handler app removed"
