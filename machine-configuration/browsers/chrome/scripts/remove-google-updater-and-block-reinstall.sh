#!/usr/bin/env bash
set -uo pipefail

updaterOwnerUsername="${1:?target username required}"
updaterOwnerUserId="$(/usr/bin/id -u "$updaterOwnerUsername")"
updaterOwnerHomeDirectory="$(/usr/bin/dscl . -read "/Users/$updaterOwnerUsername" NFSHomeDirectory | /usr/bin/sed 's/^NFSHomeDirectory: //')"

systemDomainUpdaterLaunchdLabels=(
	"com.google.GoogleUpdater.wake.system"
	"com.google.keystone.daemon"
)

guiDomainUpdaterLaunchdLabels=(
	"com.google.GoogleUpdater.wake"
	"com.google.keystone.agent"
	"com.google.keystone.xpcservice"
)

updaterLaunchdPlistPaths=(
	"/Library/LaunchDaemons/com.google.GoogleUpdater.wake.system.plist"
	"/Library/LaunchDaemons/com.google.keystone.daemon.plist"
	"/Library/LaunchAgents/com.google.keystone.agent.plist"
	"/Library/LaunchAgents/com.google.keystone.xpcservice.plist"
	"$updaterOwnerHomeDirectory/Library/LaunchAgents/com.google.GoogleUpdater.wake.plist"
	"$updaterOwnerHomeDirectory/Library/LaunchAgents/com.google.keystone.agent.plist"
	"$updaterOwnerHomeDirectory/Library/LaunchAgents/com.google.keystone.xpcservice.plist"
)

blockUpdaterInstallPath() {
	local updaterInstallPath="$1"
	local parentDirectoryOwnership="$2"
	local parentDirectory
	parentDirectory="$(/usr/bin/dirname "$updaterInstallPath")"

	/usr/bin/chflags -R nouchg "$updaterInstallPath" 2>/dev/null || true
	if [ -d "$updaterInstallPath" ]; then
		/bin/rm -rf "$updaterInstallPath"
	fi
	if [ ! -d "$parentDirectory" ]; then
		/bin/mkdir -p "$parentDirectory"
		/usr/sbin/chown "$parentDirectoryOwnership" "$parentDirectory"
	fi
	if [ ! -e "$updaterInstallPath" ]; then
		/usr/bin/touch "$updaterInstallPath"
	fi
	/usr/sbin/chown root:wheel "$updaterInstallPath"
	/bin/chmod 0444 "$updaterInstallPath"
	/usr/bin/chflags uchg "$updaterInstallPath"
}

echo "removing the Google updater and blocking its reinstall so Chrome stays pinned to the installed version..." >&2

for systemDomainUpdaterLaunchdLabel in "${systemDomainUpdaterLaunchdLabels[@]}"; do
	/bin/launchctl bootout "system/$systemDomainUpdaterLaunchdLabel" 2>/dev/null || true
	/bin/launchctl disable "system/$systemDomainUpdaterLaunchdLabel" || true
done

for guiDomainUpdaterLaunchdLabel in "${guiDomainUpdaterLaunchdLabels[@]}"; do
	/bin/launchctl bootout "gui/$updaterOwnerUserId/$guiDomainUpdaterLaunchdLabel" 2>/dev/null || true
	/bin/launchctl disable "gui/$updaterOwnerUserId/$guiDomainUpdaterLaunchdLabel" || true
done

for updaterLaunchdPlistPath in "${updaterLaunchdPlistPaths[@]}"; do
	/bin/rm -f "$updaterLaunchdPlistPath"
done

/usr/bin/pkill -f "GoogleUpdater.app/Contents/MacOS/GoogleUpdater" || true

blockUpdaterInstallPath "/Library/Application Support/Google/GoogleUpdater" "root:wheel"
blockUpdaterInstallPath "/Library/Google/GoogleSoftwareUpdate" "root:wheel"
blockUpdaterInstallPath "$updaterOwnerHomeDirectory/Library/Application Support/Google/GoogleUpdater" "$updaterOwnerUsername:staff"
blockUpdaterInstallPath "$updaterOwnerHomeDirectory/Library/Google/GoogleSoftwareUpdate" "$updaterOwnerUsername:staff"
