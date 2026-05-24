#!/usr/bin/env bash
# Mirrors the nix-managed karabiner.json into ~/.config/karabiner/karabiner.json
# only when the contents differ. Driven by SOURCE_KARABINER_JSON env var.

destinationKarabinerJsonPath="$HOME/.config/karabiner/karabiner.json"
mkdir -p "$(dirname "$destinationKarabinerJsonPath")"
if ! /usr/bin/cmp -s "$SOURCE_KARABINER_JSON" "$destinationKarabinerJsonPath"; then
	cat "$SOURCE_KARABINER_JSON" >"$destinationKarabinerJsonPath"
	chmod 644 "$destinationKarabinerJsonPath"
fi
