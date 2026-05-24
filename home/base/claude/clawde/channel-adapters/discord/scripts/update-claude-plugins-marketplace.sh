#!/usr/bin/env bash
# Fast-forward pulls the claude-plugins-official marketplace repo if present.
# Driven by MARKETPLACE_DIR and GIT_BIN env vars.

set -euo pipefail

if [ ! -d "$MARKETPLACE_DIR/.git" ]; then
	exit 0
fi

cd "$MARKETPLACE_DIR"
"$GIT_BIN" pull --ff-only origin main 2>/dev/null || true
