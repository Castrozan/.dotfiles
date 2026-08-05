#!/usr/bin/env bash
# Deploys the nix-managed glab config yaml to GLAB_CONFIG_DESTINATION,
# replacing any existing file. Driven by GLAB_CONFIG_SOURCE and
# GLAB_CONFIG_DESTINATION env vars.

set -euo pipefail
mkdir -p "$(dirname "$GLAB_CONFIG_DESTINATION")"
rm -f "$GLAB_CONFIG_DESTINATION"
cp "$GLAB_CONFIG_SOURCE" "$GLAB_CONFIG_DESTINATION"
chmod 600 "$GLAB_CONFIG_DESTINATION"
