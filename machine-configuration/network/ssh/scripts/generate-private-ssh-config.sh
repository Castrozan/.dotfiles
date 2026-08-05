#!/usr/bin/env bash
# Generates ~/.ssh/config.d/private-hosts from the agenix-decrypted
# SSH_HOSTS_FILE. If the hosts file is missing, removes the generated
# artifact so the host returns to a clean state.

set -euo pipefail
HOSTS="$SSH_HOSTS_FILE"
SSH_DIR="$HOME/.ssh"
CONFIG_DIR="$SSH_DIR/config.d"
PRIVATE_HOSTS="$CONFIG_DIR/private-hosts"

mkdir -p "$CONFIG_DIR"

if [ ! -f "$HOSTS" ]; then
	rm -f "$PRIVATE_HOSTS"
	exit 0
fi

declare -A hosts
while IFS='=' read -r key value; do
	[ -n "$key" ] && hosts["$key"]="$value"
done <"$HOSTS"

{
	if [ -n "${hosts[dellg15]:-}" ]; then
		printf 'Host dellg15\n'
		printf '    HostName %s\n' "${hosts[dellg15]}"
		printf '    User zanoni\n'
		printf '    IdentityFile ~/.ssh/id_ed25519\n\n'
	fi
} >"$PRIVATE_HOSTS"
