#!/usr/bin/env bats

setup() {
	SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/scripts/bw-session.sh"
	TEST_TEMP_DIR="$(mktemp -d)"

	export HOME="$TEST_TEMP_DIR/home"
	mkdir -p "$HOME/.secrets"
	printf 'client-id' >"$HOME/.secrets/bitwarden-client-id"
	printf 'client-secret' >"$HOME/.secrets/bitwarden-client-secret"
	printf 'master-password' >"$HOME/.secrets/bitwarden-master-password"

	PERSONAL_DATA_DIR="$TEST_TEMP_DIR/appdata/personal"
	WORK_DATA_DIR="$TEST_TEMP_DIR/appdata/work"
	REGISTRY_PATH="$TEST_TEMP_DIR/accounts.json"
	jq -n \
		--arg personalDir "$PERSONAL_DATA_DIR" \
		--arg workDir "$WORK_DATA_DIR" \
		'{
      personal: {server: null, applicationDataDirectory: $personalDir, clientIdSecret: "bitwarden-client-id", clientSecretSecret: "bitwarden-client-secret", masterPasswordSecret: "bitwarden-master-password"},
      work: {server: "https://vault.example.internal", applicationDataDirectory: $workDir, clientIdSecret: "bitwarden-client-id", clientSecretSecret: "bitwarden-client-secret", masterPasswordSecret: "bitwarden-master-password"}
    }' >"$REGISTRY_PATH"
	export BITWARDEN_ACCOUNTS_REGISTRY="$REGISTRY_PATH"

	BW_CAPTURE="$TEST_TEMP_DIR/bw-capture"
	export BW_CAPTURE
	STUB_BIN="$TEST_TEMP_DIR/bin"
	mkdir -p "$STUB_BIN"
	cat >"$STUB_BIN/bw" <<'STUB'
#!/usr/bin/env bash
case "$1" in
  status) printf '{"status":"unauthenticated"}' ;;
  config) [ "$2" = "server" ] && echo "config-server=$3 appdata=${BITWARDENCLI_APPDATA_DIR:-}" >>"$BW_CAPTURE" ;;
  login) : ;;
  unlock) echo "unlock-appdata=${BITWARDENCLI_APPDATA_DIR:-}" >>"$BW_CAPTURE"; printf 'FAKE_SESSION_TOKEN' ;;
  *) : ;;
esac
STUB
	chmod +x "$STUB_BIN/bw"
	PATH="$STUB_BIN:$PATH"
}

teardown() {
	rm -rf "$TEST_TEMP_DIR"
}

@test "errors when the account registry is missing" {
	export BITWARDEN_ACCOUNTS_REGISTRY="$TEST_TEMP_DIR/nonexistent.json"
	run bash "$SCRIPT_UNDER_TEST" personal
	[ "$status" -eq 1 ]
	[[ "$output" == *"account registry not found"* ]]
}

@test "errors and lists known accounts for an unknown account" {
	run bash "$SCRIPT_UNDER_TEST" doesnotexist
	[ "$status" -eq 1 ]
	[[ "$output" == *"unknown account 'doesnotexist'"* ]]
	[[ "$output" == *"personal"* ]]
	[[ "$output" == *"work"* ]]
}

@test "personal account unlocks its isolated data dir on the default cloud" {
	run bash "$SCRIPT_UNDER_TEST" personal
	[ "$status" -eq 0 ]
	[[ "$output" == *"FAKE_SESSION_TOKEN"* ]]
	grep -qF "config-server=https://bitwarden.com appdata=$PERSONAL_DATA_DIR" "$BW_CAPTURE"
	grep -qF "unlock-appdata=$PERSONAL_DATA_DIR" "$BW_CAPTURE"
}

@test "explicit-server account pins its own server and data dir" {
	run bash "$SCRIPT_UNDER_TEST" work
	[ "$status" -eq 0 ]
	grep -qF "config-server=https://vault.example.internal appdata=$WORK_DATA_DIR" "$BW_CAPTURE"
}

@test "defaults to the personal account when no account is given" {
	run bash "$SCRIPT_UNDER_TEST"
	[ "$status" -eq 0 ]
	grep -qF "unlock-appdata=$PERSONAL_DATA_DIR" "$BW_CAPTURE"
}
