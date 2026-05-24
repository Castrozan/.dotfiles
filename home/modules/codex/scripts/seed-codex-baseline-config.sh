#!/usr/bin/env bash
# Seeds ~/.codex/config.toml from CODEX_CONFIG_SOURCE if the user has no
# existing file. After seeding the file is mutable so the user can tweak it
# without rebuilds.

mkdir -p "$HOME/.codex"
if [ ! -f "$HOME/.codex/config.toml" ]; then
	cp "$CODEX_CONFIG_SOURCE" "$HOME/.codex/config.toml"
	chmod 644 "$HOME/.codex/config.toml"
fi
