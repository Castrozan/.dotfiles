#!/bin/bash
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
exit_code=$?

# Convert blocking exit code 2 from missing/broken hooks to non-blocking
# Only real hook logic should use exit 2 intentionally
if [[ $exit_code -eq 2 && ! -f "$HOOK_SCRIPT" ]]; then
    exit 1
fi

exit $exit_code
