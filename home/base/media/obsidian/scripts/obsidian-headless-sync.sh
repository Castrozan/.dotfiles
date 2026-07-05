#!/usr/bin/env bash

set -euo pipefail

export PATH="$NODE_BIN_DIR${PATH:+:$PATH}"
export NPM_CONFIG_PREFIX="$NPM_PREFIX"

OB_BIN="$NPM_PREFIX/bin/ob"
if [ ! -x "$OB_BIN" ]; then
	echo "obsidian-headless not installed. Run 'ob --version' to trigger install." >&2
	exit 1
fi

SYNC_LOCK_PATH="$VAULT_PATH/.obsidian/.sync.lock"
if [ -e "$SYNC_LOCK_PATH" ]; then
	if [ -n "$("$FIND_BIN" "$SYNC_LOCK_PATH" -mmin -1 2>/dev/null)" ]; then
		echo "Sync lock was touched within the last minute; another sync is active. Skipping this pass."
		exit 0
	fi
	echo "Removing abandoned sync lock idle for over a minute: $SYNC_LOCK_PATH"
	rm -rf "$SYNC_LOCK_PATH"
fi

exec "$TIMEOUT_BIN" --signal=TERM --kill-after=30s 240s "$OB_BIN" sync --path "$VAULT_PATH"
