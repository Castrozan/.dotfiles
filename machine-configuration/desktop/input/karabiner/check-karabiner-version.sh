#!/usr/bin/env bash
# Aborts activation if installed karabiner-elements is older than
# REQUIRED_KARABINER_VERSION (major-version compare). No-op if karabiner is
# not installed. Driven by REQUIRED_KARABINER_VERSION env var.

karabinerInfoPlistPath="/Applications/Karabiner-Elements.app/Contents/Info.plist"
if [[ -f "$karabinerInfoPlistPath" ]]; then
	installedKarabinerVersion=$(/usr/bin/defaults read "$karabinerInfoPlistPath" CFBundleShortVersionString 2>/dev/null || echo "0")
	installedMajorVersion="${installedKarabinerVersion%%.*}"
	requiredMajorVersion="${REQUIRED_KARABINER_VERSION%%.*}"
	if [[ "$installedMajorVersion" -lt "$requiredMajorVersion" ]]; then
		echo "ERROR: karabiner-elements $installedKarabinerVersion is too old; need >= $REQUIRED_KARABINER_VERSION for to.send_user_command support" >&2
		echo "       upgrade with: brew upgrade --cask karabiner-elements" >&2
		exit 1
	fi
fi
