#!/usr/bin/env bash
# Hook wrapper - runs hooks gracefully, failing without blocking Claude
# Exit codes: 0=success, 1=non-blocking failure (continues), 2=blocking (stops tool)

HOOK_SCRIPT="$1"
shift

if [[ -z "$HOOK_SCRIPT" ]]; then
    echo "Usage: run-hook.sh <hook-script> [args...]" >&2
    exit 1
fi

if [[ ! -f "$HOOK_SCRIPT" ]]; then
    exit 1
fi

python3 "$HOOK_SCRIPT" "$@"
