#!/usr/bin/env bash
# Compiles the workspace-window-switcher swift daemon from SWIFT_SOURCES_DIR
# and writes the binary to SWIFT_BINARY_PATH, then kicks the launchd agent so
# the new binary takes effect immediately. Driven by SWIFT_BINARY_PATH,
# SWIFT_SOURCES_DIR, OWNER_USERNAME env vars.

swiftDaemonSourceStamp="$SWIFT_SOURCES_DIR $(/usr/bin/swiftc --version 2>/dev/null | head -1)"
swiftDaemonSourceStampPath="$SWIFT_BINARY_PATH.sourcehash"
if [ -x "$SWIFT_BINARY_PATH" ] && [ "$(cat "$swiftDaemonSourceStampPath" 2>/dev/null)" = "$swiftDaemonSourceStamp" ]; then
	echo "workspace-window-switcher-daemon swift sources unchanged, skipping recompile" >&2
else
	echo "compiling workspace-window-switcher-daemon swift binary..." >&2
	mkdir -p "$(dirname "$SWIFT_BINARY_PATH")"
	swiftSourceFiles=()
	while IFS= read -r -d "" swiftSourceFile; do
		swiftSourceFiles+=("$swiftSourceFile")
	done < <(/usr/bin/find "$SWIFT_SOURCES_DIR" -name '*.swift' -not -name 'Package.swift' -not -path '*/tests/*' -print0)
	if /usr/bin/swiftc -O -o "$SWIFT_BINARY_PATH" "${swiftSourceFiles[@]}"; then
		chmod 0755 "$SWIFT_BINARY_PATH"
		printf '%s' "$swiftDaemonSourceStamp" >"$swiftDaemonSourceStampPath"
		workspaceWindowSwitcherUserId=$(/usr/bin/id -u "$OWNER_USERNAME")
		/bin/launchctl kickstart -k "gui/$workspaceWindowSwitcherUserId/com.dotfiles.workspace-window-switcher" 2>/dev/null || true
	else
		echo "workspace-window-switcher-daemon swift compile failed; leaving previous binary in place" >&2
	fi
fi
