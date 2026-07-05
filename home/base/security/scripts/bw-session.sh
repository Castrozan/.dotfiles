secretsDirectory="$HOME/.secrets"

status="$(bw status | jq -r '.status')"

if [ "$status" = "unauthenticated" ]; then
	BW_CLIENTID="$(cat "$secretsDirectory/bitwarden-client-id")"
	BW_CLIENTSECRET="$(cat "$secretsDirectory/bitwarden-client-secret")"
	export BW_CLIENTID BW_CLIENTSECRET
	bw login --apikey >/dev/null
fi

BW_PASSWORD="$(cat "$secretsDirectory/bitwarden-master-password")"
export BW_PASSWORD
bw unlock --passwordenv BW_PASSWORD --raw
