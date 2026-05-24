#!/usr/bin/env bash
# Installs the obsidian-headless npm package globally into NPM_PREFIX at
# version OB_VERSION. No-op if the desired version is already installed.
# Driven by NODE_GYP_PATH, NPM_PREFIX, OB_VERSION, NPM_BIN env vars.

set -euo pipefail
export PATH="$NODE_GYP_PATH${PATH:+:$PATH}"
export NPM_CONFIG_PREFIX="$NPM_PREFIX"
OB_BIN="$NPM_PREFIX/bin/ob"

if [ -x "$OB_BIN" ]; then
	INSTALLED_VERSION="$("$OB_BIN" --version 2>/dev/null || echo "unknown")"
	if [ "$INSTALLED_VERSION" = "$OB_VERSION" ]; then
		exit 0
	fi
fi

"$NPM_BIN" install -g "obsidian-headless@$OB_VERSION" \
	--prefix "$NPM_PREFIX" \
	--registry "https://registry.npmjs.org/"
