#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$(dirname "$GLAB_CONFIG_DESTINATION")"
rm -f "$GLAB_CONFIG_DESTINATION"
cp "$GLAB_CONFIG_SOURCE" "$GLAB_CONFIG_DESTINATION"
chmod 600 "$GLAB_CONFIG_DESTINATION"
