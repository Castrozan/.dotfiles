#!/usr/bin/env bash
set -euo pipefail

claude_settings_path="${CLAUDE_SETTINGS:-$HOME/.claude/settings.json}"
nix_source_path="${NIX_SOURCE:-$HOME/.claude/settings.json.nix-source}"
jq_bin="${JQ_BIN:-jq}"

if [ ! -f "$nix_source_path" ]; then
	exit 0
fi

if [ ! -f "$claude_settings_path" ]; then
	cp "$nix_source_path" "$claude_settings_path"
	chmod 600 "$claude_settings_path"
	exit 0
fi

chmod 600 "$claude_settings_path" 2>/dev/null || true

runtime_owned_keys_preserved_across_rebuilds='["theme","voice","voiceEnabled","extraKnownMarketplaces"]'

# shellcheck disable=SC2016
merged_settings="$(
	"$jq_bin" -n \
		--slurpfile nixSource "$nix_source_path" \
		--slurpfile currentSettings "$claude_settings_path" \
		--argjson preservedKeys "$runtime_owned_keys_preserved_across_rebuilds" \
		'$nixSource[0] * ($currentSettings[0] | with_entries(select(.key as $key | $preservedKeys | index($key))))'
)"

current_settings="$(cat "$claude_settings_path")"
if [ "$merged_settings" != "$current_settings" ]; then
	printf '%s\n' "$merged_settings" >"$claude_settings_path.tmp"
	mv "$claude_settings_path.tmp" "$claude_settings_path"
fi
chmod 600 "$claude_settings_path"
