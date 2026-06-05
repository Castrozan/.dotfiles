#!/usr/bin/env bash
set -euo pipefail

secretFile="$1"
timeoutSeconds="${2:-300}"
pollIntervalSeconds=2

elapsedSeconds=0
while [ ! -s "$secretFile" ]; do
	if [ "$elapsedSeconds" -ge "$timeoutSeconds" ]; then
		printf 'wait-for-secret: %s still empty after %ss\n' "$secretFile" "$timeoutSeconds" >&2
		exit 1
	fi
	sleep "$pollIntervalSeconds"
	elapsedSeconds=$((elapsedSeconds + pollIntervalSeconds))
done
