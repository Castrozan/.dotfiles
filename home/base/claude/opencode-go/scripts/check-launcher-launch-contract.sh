#!/usr/bin/env bash
set -eu

launcherPath="$1"
bakedClaudeBinaryPath="$2"
model="$3"
baseUrl="$4"

export HOME="$(mktemp -d)"
mkdir -p "$HOME/.secrets"
printf '%s' 'fake-opencode-go-key' >"$HOME/.secrets/opencode-api-key"
export ANTHROPIC_AUTH_TOKEN='linger-token-that-must-disappear'

fakeClaudeDirectory="$(mktemp -d)"
cat >"$fakeClaudeDirectory/claude" <<'FAKE_CLAUDE_EOF'
#!/usr/bin/env bash
printf 'auth-token=%s\n' "${ANTHROPIC_AUTH_TOKEN:-unset}"
printf 'api-key=%s\n' "${ANTHROPIC_API_KEY:-unset}"
printf 'base-url=%s\n' "${ANTHROPIC_BASE_URL:-unset}"
printf 'opus-model=%s\n' "${ANTHROPIC_DEFAULT_OPUS_MODEL:-unset}"
printf 'sonnet-model=%s\n' "${ANTHROPIC_DEFAULT_SONNET_MODEL:-unset}"
printf 'haiku-model=%s\n' "${ANTHROPIC_DEFAULT_HAIKU_MODEL:-unset}"
printf 'argv=%s\n' "$*"
exit 3
FAKE_CLAUDE_EOF
chmod +x "$fakeClaudeDirectory/claude"

rewrittenLauncher="$(mktemp)"
sed "s|$bakedClaudeBinaryPath|$fakeClaudeDirectory/claude|" "$launcherPath" >"$rewrittenLauncher"
chmod +x "$rewrittenLauncher"
grep -qF "$fakeClaudeDirectory/claude" "$rewrittenLauncher" || {
	echo "test harness failed to redirect the launcher onto the fake claude"
	exit 1
}

exitCode=0
"$rewrittenLauncher" --model 'caller-preferred-model' >output.txt || exitCode=$?
test "$exitCode" -eq 3 || {
	echo "launcher must propagate the exec'd claude exit status"
	exit 1
}

grep -qF 'auth-token=unset' output.txt || {
	echo "launcher must unset ANTHROPIC_AUTH_TOKEN before exec"
	exit 1
}
grep -qF 'api-key=fake-opencode-go-key' output.txt || {
	echo "launcher must export the API key read from ~/.secrets/opencode-api-key"
	exit 1
}
grep -qF "base-url=$baseUrl" output.txt || {
	echo "launcher must export the opencode-go base URL"
	exit 1
}
grep -qF "opus-model=$model" output.txt || {
	echo "launcher must map the opus alias to $model"
	exit 1
}
grep -qF "sonnet-model=$model" output.txt || {
	echo "launcher must map the sonnet alias to $model"
	exit 1
}
grep -qF "haiku-model=$model" output.txt || {
	echo "launcher must map the haiku alias to $model"
	exit 1
}
grep -qF "argv=--model $model --model caller-preferred-model" output.txt || {
	echo "launcher must exec claude with --model $model before the caller arguments"
	exit 1
}
