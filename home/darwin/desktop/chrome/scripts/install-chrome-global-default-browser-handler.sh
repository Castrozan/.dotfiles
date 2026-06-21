#!/usr/bin/env bash
set -euo pipefail

chromeGlobalUrlOpenerBinary="$1"
dutiBinary="$2"
handlerBundleIdentifier="$3"
handlerApplicationName="$4"

userApplicationsDirectory="$HOME/Applications"
handlerApplicationPath="$userApplicationsDirectory/$handlerApplicationName.app"
handlerInfoPlist="$handlerApplicationPath/Contents/Info.plist"
plistBuddy=/usr/libexec/PlistBuddy
launchServicesRegister=/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister

mkdir -p "$userApplicationsDirectory"

temporaryWorkingDirectory="$(mktemp -d)"
trap 'rm -rf "$temporaryWorkingDirectory"' EXIT
appleScriptSourceFile="$temporaryWorkingDirectory/chrome-global-default-browser-handler.applescript"

cat >"$appleScriptSourceFile" <<APPLESCRIPT
on open location theURL
	do shell script (quoted form of "$chromeGlobalUrlOpenerBinary") & " " & quoted form of theURL
end open location

on run
	do shell script (quoted form of "$chromeGlobalUrlOpenerBinary")
end run
APPLESCRIPT

rm -rf "$handlerApplicationPath"
/usr/bin/osacompile -o "$handlerApplicationPath" "$appleScriptSourceFile"

"$plistBuddy" -c "Delete :CFBundleIdentifier" "$handlerInfoPlist" 2>/dev/null || true
"$plistBuddy" -c "Add :CFBundleIdentifier string $handlerBundleIdentifier" "$handlerInfoPlist"
"$plistBuddy" -c "Delete :CFBundleName" "$handlerInfoPlist" 2>/dev/null || true
"$plistBuddy" -c "Add :CFBundleName string $handlerApplicationName" "$handlerInfoPlist"
"$plistBuddy" -c "Delete :LSUIElement" "$handlerInfoPlist" 2>/dev/null || true
"$plistBuddy" -c "Add :LSUIElement bool true" "$handlerInfoPlist"

"$plistBuddy" -c "Delete :CFBundleURLTypes" "$handlerInfoPlist" 2>/dev/null || true
"$plistBuddy" -c "Add :CFBundleURLTypes array" "$handlerInfoPlist"
"$plistBuddy" -c "Add :CFBundleURLTypes:0 dict" "$handlerInfoPlist"
"$plistBuddy" -c "Add :CFBundleURLTypes:0:CFBundleURLName string Web URL Forwarded To Chrome Global" "$handlerInfoPlist"
"$plistBuddy" -c "Add :CFBundleURLTypes:0:LSHandlerRank string Owner" "$handlerInfoPlist"
"$plistBuddy" -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes array" "$handlerInfoPlist"
"$plistBuddy" -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes:0 string http" "$handlerInfoPlist"
"$plistBuddy" -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes:1 string https" "$handlerInfoPlist"

"$launchServicesRegister" -f "$handlerApplicationPath"

if "$dutiBinary" -s "$handlerBundleIdentifier" http all &&
	"$dutiBinary" -s "$handlerBundleIdentifier" https all; then
	echo "INFO: $handlerApplicationName registered as the default http/https handler; confirm the macOS prompt if one appears."
else
	echo "WARN: could not set $handlerApplicationName as default browser automatically; set it manually under System Settings > Desktop & Dock > Default web browser." >&2
fi
