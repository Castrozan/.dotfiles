#!/usr/bin/env bash

set -euo pipefail

VAULT_ID="2b6bae3226c07323c77d47ea9cc25a42"
AUTH_TOKEN_SECRET="$SECRETS_DIR/obsidian-headless-auth-token"
SYNC_CONFIG_SECRET="$SECRETS_DIR/obsidian-headless-sync-config"
SYNC_CONFIG_DIRECTORY="$CONFIG_DIR/sync/$VAULT_ID"

mkdir -p "$CONFIG_DIR"
mkdir -p "$SYNC_CONFIG_DIRECTORY"

cp "$AUTH_TOKEN_SECRET" "$CONFIG_DIR/auth_token"
chmod 600 "$CONFIG_DIR/auth_token"

cp "$SYNC_CONFIG_SECRET" "$SYNC_CONFIG_DIRECTORY/config.json"
sed -i "s|\"vaultPath\": \"[^\"]*\"|\"vaultPath\": \"$VAULT_PATH\"|" "$SYNC_CONFIG_DIRECTORY/config.json"
chmod 600 "$SYNC_CONFIG_DIRECTORY/config.json"
