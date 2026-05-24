#!/usr/bin/env bash
# Runs obsidian-headless sync continuously against the local vault. Driven by
# NODE_BIN_DIR, NPM_PREFIX, VAULT_PATH env vars.

export PATH="$NODE_BIN_DIR${PATH:+:$PATH}"
export NPM_CONFIG_PREFIX="$NPM_PREFIX"

OB_BIN="$NPM_PREFIX/bin/ob"
if [ ! -x "$OB_BIN" ]; then
	echo "obsidian-headless not installed. Run 'ob --version' to trigger install." >&2
	exit 1
fi

exec "$OB_BIN" sync --continuous --path "$VAULT_PATH"
