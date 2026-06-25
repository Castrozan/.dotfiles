#!/usr/bin/env bats

setup() {
	REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../../../../.." && pwd)"
	source "$REPO_ROOT/tests/helpers/bash-script-assertions.bash"
	SCRIPT_UNDER_TEST="$(_resolve_script_under_test)"
	source "$SCRIPT_UNDER_TEST"
}

@test "rebuild script is executable" {
	assert_is_executable
}

@test "rebuild script uses strict error handling" {
	assert_uses_strict_error_handling
}

@test "rebuild script passes shellcheck" {
	assert_passes_shellcheck
}

@test "chise deploy is blocked when /etc/nixos/flake.nix is absent" {
	_etc_nixos_flake_present() { return 1; }
	run _assert_chise_not_deploying_from_bare_dotfiles chise
	[ "$status" -ne 0 ]
	[[ "$output" == *"refusing to deploy chise from bare"* ]]
}

@test "chise deploy is allowed when /etc/nixos/flake.nix is present" {
	_etc_nixos_flake_present() { return 0; }
	run _assert_chise_not_deploying_from_bare_dotfiles chise
	[ "$status" -eq 0 ]
}

@test "non-chise deploy is allowed even when /etc/nixos/flake.nix is absent" {
	_etc_nixos_flake_present() { return 1; }
	run _assert_chise_not_deploying_from_bare_dotfiles jojo
	[ "$status" -eq 0 ]
}

@test "flake ref resolves to /etc/nixos when /etc/nixos/flake.nix is present" {
	_etc_nixos_flake_present() { return 0; }
	run _resolve_nixos_flake_ref chise
	[ "$status" -eq 0 ]
	[ "$output" = "/etc/nixos#chise" ]
}

@test "flake ref resolves to bare dotfiles when /etc/nixos/flake.nix is absent" {
	_etc_nixos_flake_present() { return 1; }
	run _resolve_nixos_flake_ref chise
	[ "$status" -eq 0 ]
	[[ "$output" == *".dotfiles?submodules=1#chise" ]]
}
