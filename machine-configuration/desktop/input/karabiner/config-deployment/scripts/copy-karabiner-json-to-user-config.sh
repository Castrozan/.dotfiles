#!/usr/bin/env bash
destinationKarabinerJsonPath="$HOME/.config/karabiner/karabiner.json"
karabinerConfigChangedSentinelPath="$HOME/.local/state/karabiner-config-changed-since-last-kick"
mkdir -p "$(dirname "$destinationKarabinerJsonPath")"
mkdir -p "$(dirname "$karabinerConfigChangedSentinelPath")"
if ! /usr/bin/cmp -s "$SOURCE_KARABINER_JSON" "$destinationKarabinerJsonPath"; then
	cat "$SOURCE_KARABINER_JSON" >"$destinationKarabinerJsonPath"
	chmod 644 "$destinationKarabinerJsonPath"
	touch "$karabinerConfigChangedSentinelPath"
fi
