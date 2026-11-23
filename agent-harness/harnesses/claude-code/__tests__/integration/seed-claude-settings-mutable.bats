#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

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

@test "creates settings from nix-source when the mutable file is absent" {
	echo '{"effortLevel":"max"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r .effortLevel "$CLAUDE_SETTINGS")" = "max" ]
}

@test "drops a key removed from nix-source so a rebuild applies the deletion" {
	echo '{"effortLevel":"max","enabledPlugins":{"discord@claude-plugins-official":true},"theme":"dark"}' >"$CLAUDE_SETTINGS"
	echo '{"effortLevel":"max"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq 'has("enabledPlugins")' "$CLAUDE_SETTINGS")" = "false" ]
}

@test "preserves runtime-owned keys that nix-source does not manage" {
	echo '{"theme":"dark","voice":"alloy","voiceEnabled":true,"extraKnownMarketplaces":{"m":1}}' >"$CLAUDE_SETTINGS"
	echo '{"effortLevel":"max"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r .theme "$CLAUDE_SETTINGS")" = "dark" ]
	[ "$(jq -r .voice "$CLAUDE_SETTINGS")" = "alloy" ]
	[ "$(jq -r .voiceEnabled "$CLAUDE_SETTINGS")" = "true" ]
	[ "$(jq -r .effortLevel "$CLAUDE_SETTINGS")" = "max" ]
}

@test "keeps the model the user switched to instead of a nix-declared one" {
	echo '{"model":"claude-opus-5[1m]"}' >"$CLAUDE_SETTINGS"
	echo '{"effortLevel":"max"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r .model "$CLAUDE_SETTINGS")" = "claude-opus-5[1m]" ]
}

@test "nix-source managed values win over stale current values" {
	echo '{"language":"french"}' >"$CLAUDE_SETTINGS"
	echo '{"language":"english"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r .language "$CLAUDE_SETTINGS")" = "english" ]
}

@test "preserves the chosen effort across repeated rebuilds without a nix default" {
	echo '{"effortLevel":"medium"}' >"$CLAUDE_SETTINGS"
	echo '{"language":"english"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r .effortLevel "$CLAUDE_SETTINGS")" = "medium" ]
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r .effortLevel "$CLAUDE_SETTINGS")" = "medium" ]
}

@test "keeps the effort the user chose over a nix-declared value" {
	echo '{"effortLevel":"medium"}' >"$CLAUDE_SETTINGS"
	echo '{"effortLevel":"max"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r .effortLevel "$CLAUDE_SETTINGS")" = "medium" ]
}

@test "preserves per-model effort selections across repeated rebuilds" {
	echo '{"model":"sonnet","modelSettings":{"claude-sonnet-5":{"effortLevel":"medium"},"claude-opus-5":{"effortLevel":"high"}}}' >"$CLAUDE_SETTINGS"
	echo '{"language":"english"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r '.modelSettings["claude-sonnet-5"].effortLevel' "$CLAUDE_SETTINGS")" = "medium" ]
	[ "$(jq -r '.modelSettings["claude-opus-5"].effortLevel' "$CLAUDE_SETTINGS")" = "high" ]
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq -r '.modelSettings["claude-sonnet-5"].effortLevel' "$CLAUDE_SETTINGS")" = "medium" ]
	[ "$(jq -r '.modelSettings["claude-opus-5"].effortLevel' "$CLAUDE_SETTINGS")" = "high" ]
	[ "$(jq -r .model "$CLAUDE_SETTINGS")" = "sonnet" ]
}

@test "leaves effort unset when no effort has been chosen" {
	echo '{"language":"english"}' >"$NIX_SOURCE"
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq 'has("effortLevel")' "$CLAUDE_SETTINGS")" = "false" ]
	_run_seed
	[ "$status" -eq 0 ]
	[ "$(jq 'has("effortLevel")' "$CLAUDE_SETTINGS")" = "false" ]
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
