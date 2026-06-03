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

export PYTHONPYCACHEPREFIX="${XDG_CACHE_HOME:-$HOME/.cache}/claude-code-hooks/pycache"

python3 "$HOOK_SCRIPT" "$@"
