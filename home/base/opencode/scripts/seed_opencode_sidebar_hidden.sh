#!/usr/bin/env bash

set -euo pipefail

KV_FILE="${1:?usage: seed_opencode_sidebar_hidden.sh <kv.json path>}"
STATE_DIRECTORY="$(dirname "$KV_FILE")"

mkdir -p "$STATE_DIRECTORY"

if [ ! -f "$KV_FILE" ]; then
	echo '{"sidebar":"hide"}' >"$KV_FILE"
	exit 0
fi

jq 'if has("sidebar") then . else . + {"sidebar":"hide"} end' "$KV_FILE" | sponge "$KV_FILE"
