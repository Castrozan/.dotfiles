#!/usr/bin/env bash
# Maintains $HOME/.claude/settings.json as a writable file seeded from the
# nix-source (immutable, read-only). On each activation, recursive-merges
# the user's runtime tweaks with nix-source so nix-controlled defaults win,
# then fully replaces the .hooks block with nix-source.hooks so hooks
# removed from nix are also removed from settings.json (recursive merge
# alone leaks stale keys). Driven by JQ_BIN env var.

CLAUDE_SETTINGS="$HOME/.claude/settings.json"
NIX_SOURCE="$HOME/.claude/settings.json.nix-source"
if [ -f "$NIX_SOURCE" ]; then
	if [ -f "$CLAUDE_SETTINGS" ]; then
		chmod 600 "$CLAUDE_SETTINGS" 2>/dev/null || true
		# shellcheck disable=SC2016 # $current/$nix are jq variables, not shell
		MERGED_SETTINGS=$("$JQ_BIN" -s '.[0] as $current | .[1] as $nix | ($current * $nix) | .hooks = $nix.hooks' "$CLAUDE_SETTINGS" "$NIX_SOURCE")
		CURRENT_SETTINGS=$(cat "$CLAUDE_SETTINGS")
		if [ "$MERGED_SETTINGS" != "$CURRENT_SETTINGS" ]; then
			echo "$MERGED_SETTINGS" >"$CLAUDE_SETTINGS.tmp" && mv "$CLAUDE_SETTINGS.tmp" "$CLAUDE_SETTINGS"
		fi
	else
		cp "$NIX_SOURCE" "$CLAUDE_SETTINGS"
	fi
	chmod 600 "$CLAUDE_SETTINGS"
fi
