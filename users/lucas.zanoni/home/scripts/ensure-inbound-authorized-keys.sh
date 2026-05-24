#!/usr/bin/env bash
# Adds every key in INBOUND_AUTHORIZED_KEYS (newline-separated env var) to
# ~/.ssh/authorized_keys if not already present. Idempotent.

set -euo pipefail
SSH_DIR="$HOME/.ssh"
AUTHORIZED="$SSH_DIR/authorized_keys"

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"
touch "$AUTHORIZED"
chmod 600 "$AUTHORIZED"

while IFS= read -r key; do
	[ -z "$key" ] && continue
	if ! grep -qxF "$key" "$AUTHORIZED"; then
		printf '%s\n' "$key" >>"$AUTHORIZED"
	fi
done <<<"$INBOUND_AUTHORIZED_KEYS"
