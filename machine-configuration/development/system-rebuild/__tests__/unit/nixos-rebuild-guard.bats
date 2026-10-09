#!/usr/bin/env bats

setup() {
	REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../../../.." && pwd)"
	source "$REPO_ROOT/repository/verification/helpers/bash-script-assertions.bash"
	SCRIPT_UNDER_TEST="$REPO_ROOT/machine-configuration/development/system-rebuild/scripts/nixos-rebuild-guard"
	export SYSTEM_REBUILD_LOCK_GUARD="$BATS_TEST_TMPDIR/system-rebuild-lock"
	printf '#!/usr/bin/env bash\nexec "$@"\n' >"$SYSTEM_REBUILD_LOCK_GUARD"
	chmod +x "$SYSTEM_REBUILD_LOCK_GUARD"
}

@test "nixos-rebuild guard is executable" {
	assert_is_executable
}

@test "nixos-rebuild guard uses strict error handling" {
	assert_uses_strict_error_handling
}

@test "nixos-rebuild guard passes shellcheck" {
	assert_passes_shellcheck
}

@test "nixos-rebuild guard blocks switch without the rebuild sentinel" {
	run env -u DOTFILES_REBUILD_WRAPPER REAL_NIXOS_REBUILD=true bash "$SCRIPT_UNDER_TEST" switch
	[ "$status" -ne 0 ]
	[[ "$output" == *"is blocked on this host"* ]]
}

@test "nixos-rebuild guard blocks boot without the rebuild sentinel" {
	run env -u DOTFILES_REBUILD_WRAPPER REAL_NIXOS_REBUILD=true bash "$SCRIPT_UNDER_TEST" boot
	[ "$status" -ne 0 ]
}

@test "nixos-rebuild guard blocks test without the rebuild sentinel" {
	run env -u DOTFILES_REBUILD_WRAPPER REAL_NIXOS_REBUILD=true bash "$SCRIPT_UNDER_TEST" test
	[ "$status" -ne 0 ]
}

@test "nixos-rebuild guard allows a read-only action without the sentinel" {
	run env -u DOTFILES_REBUILD_WRAPPER REAL_NIXOS_REBUILD=true bash "$SCRIPT_UNDER_TEST" list-generations
	[ "$status" -eq 0 ]
}

@test "nixos-rebuild guard passes switch through when the rebuild sentinel is set" {
	run env DOTFILES_REBUILD_WRAPPER=1 REAL_NIXOS_REBUILD=true bash "$SCRIPT_UNDER_TEST" switch
	[ "$status" -eq 0 ]
}
