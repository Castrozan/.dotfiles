#!/usr/bin/env bash
set -eu

launcherPath="$1"
model="$2"
baseUrl="$3"
bakedClaudeBinaryPath="$4"

launcherScript="$(cat "$launcherPath")"

grep -qF 'unset ANTHROPIC_AUTH_TOKEN' <<<"$launcherScript" || {
	echo "launcher must unset ANTHROPIC_AUTH_TOKEN, which the opencode-go endpoint rejects as bearer auth"
	exit 1
}
grep -qF 'ANTHROPIC_API_KEY="$(cat' <<<"$launcherScript" || {
	echo "launcher must read the API key from a file at runtime rather than embedding it"
	exit 1
}
grep -qF '.secrets/opencode-api-key' <<<"$launcherScript" || {
	echo "launcher must reference the agenix-deployed ~/.secrets/opencode-api-key"
	exit 1
}
grep -qF "ANTHROPIC_BASE_URL=\"$baseUrl\"" <<<"$launcherScript" || {
	echo "launcher must point ANTHROPIC_BASE_URL at the opencode-go Anthropic-compatible endpoint"
	exit 1
}
grep -qF "ANTHROPIC_DEFAULT_OPUS_MODEL=\"$model\"" <<<"$launcherScript" || {
	echo "launcher must map the opus alias to $model"
	exit 1
}
grep -qF "ANTHROPIC_DEFAULT_SONNET_MODEL=\"$model\"" <<<"$launcherScript" || {
	echo "launcher must map the sonnet alias to $model"
	exit 1
}
grep -qF "ANTHROPIC_DEFAULT_HAIKU_MODEL=\"$model\"" <<<"$launcherScript" || {
	echo "launcher must map the haiku alias to $model"
	exit 1
}
grep -qF "exec $bakedClaudeBinaryPath --model \"$model\" \"\$@\"" <<<"$launcherScript" || {
	echo "launcher must exec the configured claude binary with --model $model before the caller arguments"
	exit 1
}
if grep -qF 'set -x' <<<"$launcherScript"; then
	echo "launcher must not enable xtrace, which would dump the API key into output"
	exit 1
fi
