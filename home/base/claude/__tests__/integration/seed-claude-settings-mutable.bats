#!/usr/bin/env bats

load '../../../../../__tests__/helpers/bash-script-assertions'

SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)/../../settings/workarounds/seed-claude-settings-mutable.sh"

setup() {
	TEST_DIRECTORY="$(mktemp -d)"
	export CLAUDE_SETTINGS="$TEST_DIRECTORY/settings.json"
	export NIX_SOURCE="$TEST_DIRECTORY/settings.json.nix-source"
	export JQ_BIN="$(command -v jq)"
}

teardown() {
	rm -rf "$TEST_DIRECTORY"
}

_run_seed() {
	run bash "$SCRIPT_UNDER_TEST"
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "uses strict error handling" {
	assert_uses_strict_error_handling
}

@test "creates settings from nix-source when the mutable file is absent" {
	echo '{"model":"opus"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r .model "$CLAUDE_SETTINGS")" = "opus" ]
}

@test "drops a key removed from nix-source so a rebuild applies the deletion" {
	echo '{"model":"opus","enabledPlugins":{"discord@claude-plugins-official":true},"theme":"dark"}' >"$CLAUDE_SETTINGS"
	echo '{"model":"opus"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq 'has("enabledPlugins")' "$CLAUDE_SETTINGS")" = "false" ]
}

@test "preserves runtime-owned keys that nix-source does not manage" {
	echo '{"theme":"dark","voice":"alloy","voiceEnabled":true,"extraKnownMarketplaces":{"m":1}}' >"$CLAUDE_SETTINGS"
	echo '{"model":"opus"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r .theme "$CLAUDE_SETTINGS")" = "dark" ]
	[ "$(jq -r .voice "$CLAUDE_SETTINGS")" = "alloy" ]
	[ "$(jq -r .voiceEnabled "$CLAUDE_SETTINGS")" = "true" ]
	[ "$(jq -r .model "$CLAUDE_SETTINGS")" = "opus" ]
}

@test "nix-source managed values win over stale current values" {
	echo '{"model":"sonnet"}' >"$CLAUDE_SETTINGS"
	echo '{"model":"opus"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r .model "$CLAUDE_SETTINGS")" = "opus" ]
}

@test "hooks come entirely from nix-source not the mutable file" {
	echo '{"hooks":{"Stop":[{"stale":true}]}}' >"$CLAUDE_SETTINGS"
	echo '{"hooks":{"PreToolUse":[{"fresh":true}]}}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq 'has("Stop") | not' <(jq .hooks "$CLAUDE_SETTINGS"))" = "true" ]
	[ "$(jq -r '.hooks.PreToolUse[0].fresh' "$CLAUDE_SETTINGS")" = "true" ]
}

@test "no-op when nix-source is absent" {
	echo '{"model":"keep-me"}' >"$CLAUDE_SETTINGS"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r .model "$CLAUDE_SETTINGS")" = "keep-me" ]
}
