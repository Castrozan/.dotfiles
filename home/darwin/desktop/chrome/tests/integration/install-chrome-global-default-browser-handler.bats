#!/usr/bin/env bats

load '../../../../../../tests/helpers/bash-script-assertions'

SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)/../../scripts/install-chrome-global-default-browser-handler.sh"

setup() {
	TEST_DIRECTORY="$(mktemp -d)"
	ORIGINAL_HOME="$HOME"
	export HOME="$TEST_DIRECTORY"

	HANDLER_BUNDLE_IDENTIFIER="com.lucaszanoni.chrome-global-link-handler-test"
	HANDLER_APPLICATION_NAME="Chrome Global Link Handler Test"
	HANDLER_INFO_PLIST="$HOME/Applications/$HANDLER_APPLICATION_NAME.app/Contents/Info.plist"
	OPENER_BINARY="$TEST_DIRECTORY/open-url-in-chrome-global"

	SUCCESSFUL_DUTI_STUB="$TEST_DIRECTORY/duti-success"
	printf '#!/usr/bin/env bash\nexit 0\n' >"$SUCCESSFUL_DUTI_STUB"
	chmod +x "$SUCCESSFUL_DUTI_STUB"

	FAILING_DUTI_STUB="$TEST_DIRECTORY/duti-fail"
	printf '#!/usr/bin/env bash\nexit 1\n' >"$FAILING_DUTI_STUB"
	chmod +x "$FAILING_DUTI_STUB"
}

teardown() {
	export HOME="$ORIGINAL_HOME"
	rm -rf "$TEST_DIRECTORY"
}

_run_install_with_duti() {
	run bash "$SCRIPT_UNDER_TEST" \
		"$OPENER_BINARY" \
		"$1" \
		"$HANDLER_BUNDLE_IDENTIFIER" \
		"$HANDLER_APPLICATION_NAME"
}

_print_plist_entry() {
	/usr/libexec/PlistBuddy -c "Print $1" "$HANDLER_INFO_PLIST"
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "uses strict error handling" {
	assert_uses_strict_error_handling
}

@test "builds the handler app and sets the bundle identifier on a fresh osacompile droplet" {
	_run_install_with_duti "$SUCCESSFUL_DUTI_STUB"
	[ "$status" -eq 0 ]
	[ -d "$HOME/Applications/$HANDLER_APPLICATION_NAME.app" ]
	[ "$(_print_plist_entry ':CFBundleIdentifier')" = "$HANDLER_BUNDLE_IDENTIFIER" ]
}

@test "declares http and https url schemes so launchservices offers it as a web browser" {
	_run_install_with_duti "$SUCCESSFUL_DUTI_STUB"
	[ "$status" -eq 0 ]
	[ "$(_print_plist_entry ':CFBundleURLTypes:0:CFBundleURLSchemes:0')" = "http" ]
	[ "$(_print_plist_entry ':CFBundleURLTypes:0:CFBundleURLSchemes:1')" = "https" ]
	[ "$(_print_plist_entry ':CFBundleURLTypes:0:LSHandlerRank')" = "Owner" ]
}

@test "is idempotent across repeated installs" {
	_run_install_with_duti "$SUCCESSFUL_DUTI_STUB"
	[ "$status" -eq 0 ]
	_run_install_with_duti "$SUCCESSFUL_DUTI_STUB"
	[ "$status" -eq 0 ]
	[ "$(_print_plist_entry ':CFBundleIdentifier')" = "$HANDLER_BUNDLE_IDENTIFIER" ]
}

@test "builds under the gnu coreutils mktemp that home-manager activation puts on PATH" {
	GNU_STRICT_MKTEMP_DIRECTORY="$TEST_DIRECTORY/gnu-strict-mktemp"
	mkdir -p "$GNU_STRICT_MKTEMP_DIRECTORY"
	cat >"$GNU_STRICT_MKTEMP_DIRECTORY/mktemp" <<'STUB'
#!/usr/bin/env bash
if [ "$1" = "-d" ]; then
	exec /usr/bin/mktemp -d "${@:2}"
fi
for argument in "$@"; do
	case "$argument" in
	-*) ;;
	*XXX*) ;;
	*)
		echo "mktemp: too few X's in template '$argument'" >&2
		exit 1
		;;
	esac
done
exec /usr/bin/mktemp "$@"
STUB
	chmod +x "$GNU_STRICT_MKTEMP_DIRECTORY/mktemp"
	run env PATH="$GNU_STRICT_MKTEMP_DIRECTORY:$PATH" bash "$SCRIPT_UNDER_TEST" \
		"$OPENER_BINARY" \
		"$SUCCESSFUL_DUTI_STUB" \
		"$HANDLER_BUNDLE_IDENTIFIER" \
		"$HANDLER_APPLICATION_NAME"
	[ "$status" -eq 0 ]
	[ -d "$HOME/Applications/$HANDLER_APPLICATION_NAME.app" ]
}

@test "exits zero and still installs the app when duti registration fails so a manual-confirmation case does not loop the rebuild" {
	_run_install_with_duti "$FAILING_DUTI_STUB"
	[ "$status" -eq 0 ]
	[ -d "$HOME/Applications/$HANDLER_APPLICATION_NAME.app" ]
	[[ "$output" == *"set it manually"* ]]
}
