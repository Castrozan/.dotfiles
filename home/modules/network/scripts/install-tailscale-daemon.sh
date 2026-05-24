#!/usr/bin/env bash
# Installs tailscale via Homebrew on macOS if no tailscale binary is already
# present on a known path. Driven by TAILSCALE_CANDIDATE_PATHS and
# BREW_CANDIDATE_PATHS env vars (space-separated absolute paths).

# shellcheck disable=SC2086  # intentional word splitting on candidate path lists
for candidate in $TAILSCALE_CANDIDATE_PATHS; do
	if [ -x "$candidate" ]; then
		exit 0
	fi
done

BREW=""
# shellcheck disable=SC2086
for candidate in $BREW_CANDIDATE_PATHS; do
	if [ -x "$candidate" ]; then
		BREW="$candidate"
		break
	fi
done

if [ -z "$BREW" ]; then
	echo "[tailscale] ERROR: Homebrew is required to install tailscale on macOS." >&2
	echo "[tailscale]        Install brew first: https://brew.sh" >&2
	exit 1
fi

if "$BREW" list --formula tailscale >/dev/null 2>&1; then
	echo "[tailscale] formula installed but symlink missing, relinking..."
	"$BREW" link --overwrite tailscale
else
	echo "[tailscale] CLI not found, installing via Homebrew..."
	"$BREW" install tailscale
fi

echo ""
echo "[tailscale] To start the daemon and join the tailnet:"
echo "[tailscale]   sudo brew services start tailscale"
echo "[tailscale]   sudo tailscale up"
echo ""
echo "[tailscale] A browser will open to authenticate. Use the same Tailscale"
echo "[tailscale] account as your other devices in the tailnet."
