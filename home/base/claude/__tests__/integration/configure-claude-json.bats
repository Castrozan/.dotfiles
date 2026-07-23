#!/usr/bin/env bats

load '../../../../../__tests__/helpers/bash-script-assertions'

SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)/../../settings/configure-claude-json.sh"

setup() {
	TEST_DIRECTORY="$(mktemp -d)"
	export HOME="$TEST_DIRECTORY"
	export JQ_BIN="$(command -v jq)"
	export TRUSTED_PARENT_DIRECTORIES=""
	export TRUSTED_DIRECTORIES=""
}

teardown() {
	rm -rf "$TEST_DIRECTORY"
}

_run_configure() {
	run bash "$SCRIPT_UNDER_TEST"
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "creates a native install-method file when .claude.json is absent" {
	_run_configure
	[ "$status" -eq 0 ]
	[ "$(jq -r .installMethod "$HOME/.claude.json")" = "native" ]
}

@test "leaves an invalid .claude.json untouched" {
	printf 'not json' >"$HOME/.claude.json"
	_run_configure
	[ "$status" -eq 0 ]
	[ "$(cat "$HOME/.claude.json")" = "not json" ]
}

@test "pins every fable promo key and leaves non-fable impressions untouched" {
	echo '{"announcementImpressions":{"fable-arbitrary":3,"other-promo":5}}' >"$HOME/.claude.json"
	_run_configure
	[ "$status" -eq 0 ]
	[ "$(jq '.announcementImpressions["fable-arbitrary"]' "$HOME/.claude.json")" = "9999999" ]
	[ "$(jq '.announcementImpressions["fable-5-promo-2"]' "$HOME/.claude.json")" = "9999999" ]
	[ "$(jq '.announcementImpressions["fable-5-promo-2-2"]' "$HOME/.claude.json")" = "9999999" ]
	[ "$(jq '.announcementImpressions["other-promo"]' "$HOME/.claude.json")" = "5" ]
}

@test "seeds the known fable promo keys when announcementImpressions is absent" {
	echo '{"installMethod":"native"}' >"$HOME/.claude.json"
	_run_configure
	[ "$status" -eq 0 ]
	[ "$(jq '.announcementImpressions["fable-5-promo-2"]' "$HOME/.claude.json")" = "9999999" ]
	[ "$(jq '.announcementImpressions["fable-5-promo-2-2"]' "$HOME/.claude.json")" = "9999999" ]
}
