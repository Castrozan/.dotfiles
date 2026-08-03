#!/usr/bin/env bash
set -eu

launcherPath="$1"

export HOME="$(mktemp -d)"

exitCode=0
"$launcherPath" >output.txt 2>&1 || exitCode=$?
test "$exitCode" -ne 0 || {
	echo "launcher must fail when the API key file is absent"
	exit 1
}
grep -qF '.secrets/opencode-api-key' output.txt || {
	echo "launcher failure must name the missing API key file"
	exit 1
}

mkdir -p "$HOME/.secrets/opencode-api-key"
exitCode=0
"$launcherPath" >output.txt 2>&1 || exitCode=$?
test "$exitCode" -ne 0 || {
	echo "launcher must fail when the API key path is not a regular readable file"
	exit 1
}
grep -qF '.secrets/opencode-api-key' output.txt || {
	echo "launcher failure must name the unreadable API key file"
	exit 1
}
