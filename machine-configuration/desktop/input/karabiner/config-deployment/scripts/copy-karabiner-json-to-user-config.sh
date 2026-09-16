#!/usr/bin/env bash
# Mirrors the nix-managed karabiner.json into ~/.config/karabiner/karabiner.json
# only when the contents differ. Driven by SOURCE_KARABINER_JSON env var. On a real
# change, drops a sentinel so the karabiner user agents are kicked only when the
# config actually changed - a kick restarts karabiner and briefly opens a window
# where the Ctrl->Cmd remap is not yet excluded in terminals, hijacking Ctrl+C and
# the tmux prefix, so unrelated rebuilds must not trigger it.

destinationKarabinerJsonPath="$HOME/.config/karabiner/karabiner.json"
karabinerConfigChangedSentinelPath="$HOME/.local/state/karabiner-config-changed-since-last-kick"
mkdir -p "$(dirname "$destinationKarabinerJsonPath")"
mkdir -p "$(dirname "$karabinerConfigChangedSentinelPath")"
if ! /usr/bin/cmp -s "$SOURCE_KARABINER_JSON" "$destinationKarabinerJsonPath"; then
	cat "$SOURCE_KARABINER_JSON" >"$destinationKarabinerJsonPath"
	chmod 644 "$destinationKarabinerJsonPath"
	touch "$karabinerConfigChangedSentinelPath"
fi
