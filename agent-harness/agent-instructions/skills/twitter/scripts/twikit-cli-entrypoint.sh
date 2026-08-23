#!/usr/bin/env bash
set -euo pipefail

VENV="$TWIKIT_VIRTUALENV_PATH"

INSTALLED_TWIKIT_VERSION=$("$VENV/bin/pip" show twikit 2>/dev/null | grep -oP 'Version: \K.*' || echo "none")
if [ ! -f "$VENV/bin/python" ] || [ "$INSTALLED_TWIKIT_VERSION" != "$TWIKIT_VERSION" ]; then
	echo "[nix] Installing twikit $TWIKIT_VERSION..." >&2
	python -m venv "$VENV" 2>/dev/null || true
	"$VENV/bin/pip" install --quiet --upgrade "twikit==$TWIKIT_VERSION" pycryptodome secretstorage >&2
	TWIKIT_CLIENT="$VENV/lib/python3.12/site-packages/twikit/client/client.py"
	if [ -f "$TWIKIT_CLIENT" ]; then
		sed -i "s/\['itemContent'\]\['value'\]/['value']/g" "$TWIKIT_CLIENT"
	fi
	TWIKIT_USER="$VENV/lib/python3.12/site-packages/twikit/user.py"
	if [ -f "$TWIKIT_USER" ]; then
		sed -i "s/\['description'\]\['urls'\]/['description'].get('urls', [])/g; s/legacy\['pinned_tweet_ids_str'\]/legacy.get('pinned_tweet_ids_str', [])/g; s/legacy\['withheld_in_countries'\]/legacy.get('withheld_in_countries', [])/g" "$TWIKIT_USER"
	fi
	python "$TWIKIT_SCRIPTS_DIRECTORY/patch-twikit-transaction.py" "$VENV"
fi

if [ ! -f "$TWIKIT_COOKIES_PATH" ] && [ -f "$TWIKIT_SECRETS_DIRECTORY/x-cookies" ]; then
	mkdir -p "$(dirname "$TWIKIT_COOKIES_PATH")"
	cp "$TWIKIT_SECRETS_DIRECTORY/x-cookies" "$TWIKIT_COOKIES_PATH"
	chmod 600 "$TWIKIT_COOKIES_PATH"
	echo "[nix] Seeded cookies from agenix secret" >&2
fi

export TWIKIT_USERNAME_FILE="$TWIKIT_SECRETS_DIRECTORY/x-username"
export TWIKIT_EMAIL_FILE="$TWIKIT_SECRETS_DIRECTORY/x-email"
export TWIKIT_PASSWORD_FILE="$TWIKIT_SECRETS_DIRECTORY/x-password"

if [ "${1:-}" = "extract-cookies" ]; then
	exec "$VENV/bin/python" "$TWIKIT_SCRIPTS_DIRECTORY/extract-x-cookies.py"
fi

exec "$VENV/bin/python" "$TWIKIT_SCRIPTS_DIRECTORY/twikit-cli.py" "$@"
