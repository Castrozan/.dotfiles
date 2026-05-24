#!/usr/bin/env bash
# Marks Claude workspaces as trusted in $HOME/.claude.json. Trusts each
# immediate child directory of TRUSTED_PARENT_DIRS (newline-separated) and
# each path in TRUSTED_DIRS (newline-separated). No-op if .claude.json is
# missing. Driven by TRUSTED_PARENT_DIRS, TRUSTED_DIRS, JQ_BIN env vars.

F="$HOME/.claude.json"
[ -f "$F" ] || exit 0

trust_path() {
	"$JQ_BIN" --arg path "$1" '.projects[$path].hasTrustDialogAccepted = true' "$F" >"$F.tmp" && mv "$F.tmp" "$F"
}

while IFS= read -r parentDir; do
	[ -z "$parentDir" ] && continue
	if [ -d "$parentDir" ]; then
		for d in "$parentDir"/*/; do
			d="${d%/}"
			[ -d "$d" ] && trust_path "$d"
		done
	fi
done <<<"$TRUSTED_PARENT_DIRS"

while IFS= read -r dir; do
	[ -z "$dir" ] && continue
	trust_path "$dir"
done <<<"$TRUSTED_DIRS"
