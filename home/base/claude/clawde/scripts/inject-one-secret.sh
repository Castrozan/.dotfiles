#!/usr/bin/env bash
# Reads a secret from $1 and writes it as a .env file under $2 using the
# environment variable name $3. No-op if the secret file is missing or empty.

tokenFile="$1"
envDir="$2"
envVarName="$3"
envFile="$envDir/.env"

if [ -f "$tokenFile" ]; then
	SECRET_VALUE="$(cat "$tokenFile")"
	if [ -n "$SECRET_VALUE" ]; then
		mkdir -p "$envDir"
		printf '%s=%s\n' "$envVarName" "$SECRET_VALUE" >"$envFile"
		chmod 600 "$envFile"
	fi
fi
