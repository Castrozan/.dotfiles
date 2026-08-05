accountName="${1:-personal}"
registryPath="${BITWARDEN_ACCOUNTS_REGISTRY:-$HOME/.config/bitwarden-cli/accounts.json}"
secretsDirectory="$HOME/.secrets"

if [ ! -f "$registryPath" ]; then
	echo "bw-session: account registry not found at $registryPath" >&2
	exit 1
fi

if ! accountEntry="$(jq -e --arg account "$accountName" '.[$account]' "$registryPath")"; then
	echo "bw-session: unknown account '$accountName'; known accounts: $(jq -r 'keys | join(", ")' "$registryPath")" >&2
	exit 1
fi

applicationDataDirectory="$(jq -r '.applicationDataDirectory' <<<"$accountEntry")"
server="$(jq -r '.server // empty' <<<"$accountEntry")"
clientIdSecret="$(jq -r '.clientIdSecret' <<<"$accountEntry")"
clientSecretSecret="$(jq -r '.clientSecretSecret' <<<"$accountEntry")"
masterPasswordSecret="$(jq -r '.masterPasswordSecret' <<<"$accountEntry")"

mkdir -p "$applicationDataDirectory"
export BITWARDENCLI_APPDATA_DIR="$applicationDataDirectory"

status="$(bw status | jq -r '.status')"

if [ "$status" = "unauthenticated" ]; then
	if [ -n "$server" ]; then
		bw config server "$server" >/dev/null
	else
		bw config server https://bitwarden.com >/dev/null
	fi
	BW_CLIENTID="$(cat "$secretsDirectory/$clientIdSecret")"
	BW_CLIENTSECRET="$(cat "$secretsDirectory/$clientSecretSecret")"
	export BW_CLIENTID BW_CLIENTSECRET
	bw login --apikey >/dev/null
fi

BW_PASSWORD="$(cat "$secretsDirectory/$masterPasswordSecret")"
export BW_PASSWORD
bw unlock --passwordenv BW_PASSWORD --raw
