#!/usr/bin/env bash
# Compiles the workspace-window-switcher swift daemon from SWIFT_SOURCES_DIR
# and writes the binary to SWIFT_BINARY_PATH, then kicks the launchd agent so
# the new binary takes effect immediately. Driven by SWIFT_BINARY_PATH,
# SWIFT_SOURCES_DIR, OWNER_USERNAME env vars.

echo "compiling workspace-window-switcher-daemon swift binary..." >&2
mkdir -p "$(dirname "$SWIFT_BINARY_PATH")"
swiftSourceFiles=()
while IFS= read -r -d "" swiftSourceFile; do
	swiftSourceFiles+=("$swiftSourceFile")
done < <(/usr/bin/find "$SWIFT_SOURCES_DIR" -name '*.swift' -not -name 'Package.swift' -not -path '*/tests/*' -print0)
/usr/bin/swiftc -O -o "$SWIFT_BINARY_PATH" "${swiftSourceFiles[@]}"
chmod 0755 "$SWIFT_BINARY_PATH"
workspaceWindowSwitcherUserId=$(/usr/bin/id -u "$OWNER_USERNAME")
/bin/launchctl kickstart -k "gui/$workspaceWindowSwitcherUserId/com.dotfiles.workspace-window-switcher" 2>/dev/null || true
