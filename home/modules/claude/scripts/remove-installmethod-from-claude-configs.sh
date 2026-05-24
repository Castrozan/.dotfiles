#!/usr/bin/env bash
# Strips .installMethod from claude config files so the in-app "switch install
# method" prompt does not appear. Skips files that fail jq parse. Driven by
# JQ_BIN env var.

for TARGET_FILE in "$HOME/.claude.json" "$HOME/.claude/settings.json"; do
	if [ -f "$TARGET_FILE" ]; then
		if ! "$JQ_BIN" '.' "$TARGET_FILE" >/dev/null 2>&1; then
			echo "WARNING: $TARGET_FILE is corrupt, skipping patch" >&2
		else
			if "$JQ_BIN" -e '.installMethod' "$TARGET_FILE" >/dev/null 2>&1; then
				PATCHED_CONTENT=$("$JQ_BIN" 'del(.installMethod)' "$TARGET_FILE")
				echo "$PATCHED_CONTENT" >"$TARGET_FILE.tmp" && mv "$TARGET_FILE.tmp" "$TARGET_FILE"
			fi
		fi
	fi
done
