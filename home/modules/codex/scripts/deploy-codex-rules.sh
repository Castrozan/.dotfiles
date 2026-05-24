#!/usr/bin/env bash
# Appends each codex prefix_rule to ~/.codex/rules/default.rules if it is not
# already present. Idempotent.

set -euo pipefail

rules_file="$HOME/.codex/rules/default.rules"
rules_dir="$(dirname "$rules_file")"
mkdir -p "$rules_dir"
touch "$rules_file"

want_lines=(
	'prefix_rule(pattern=["docker", "run"], decision="allow")'
	'prefix_rule(pattern=["docker", "compose", "up"], decision="allow")'
	'prefix_rule(pattern=["glab", "mr", "view"], decision="allow")'
	'prefix_rule(pattern=["glab", "mr", "note"], decision="allow")'
	'prefix_rule(pattern=["rm", "-f", "docs/redis-local-testing.md", "devenv.nix"], decision="allow")'
	'prefix_rule(pattern=["bin/rebuild"], decision="allow")'
	'prefix_rule(pattern=["./bin/rebuild"], decision="allow")'
)

tmp="$(mktemp)"
cp "$rules_file" "$tmp"

for line in "${want_lines[@]}"; do
	if ! grep -Fqx "$line" "$tmp"; then
		printf '%s\n' "$line" >>"$tmp"
	fi
done

mv "$tmp" "$rules_file"
