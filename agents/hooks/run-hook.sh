#!/usr/bin/env bash

set -Eeuo pipefail

readonly HOOK_SCRIPT="$1"
shift

if [[ -z "$HOOK_SCRIPT" ]]; then
	echo "Usage: run-hook.sh <hook-script> [args...]" >&2
	exit 1
fi

if [[ ! -f "$HOOK_SCRIPT" ]]; then
	exit 1
fi

python3 "$HOOK_SCRIPT" "$@"
