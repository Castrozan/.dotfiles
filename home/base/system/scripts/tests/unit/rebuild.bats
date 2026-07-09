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
	run _assert_chise_not_deploying_from_bare_dotfiles kira
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

@test "zanoni-system sync is skipped for non-chise hosts" {
	_zanoni_system_flake_present() { return 0; }
	_etc_nixos_flake_matches_zanoni_system() { return 1; }
	_sudo() { echo "SUDO_CALLED"; }
	run _sync_etc_nixos_flake_from_zanoni_system kira
	[ "$status" -eq 0 ]
	[[ "$output" != *"SUDO_CALLED"* ]]
}

@test "zanoni-system sync is skipped when the zanoni-system flake is absent" {
	_zanoni_system_flake_present() { return 1; }
	_etc_nixos_flake_matches_zanoni_system() { return 1; }
	_sudo() { echo "SUDO_CALLED"; }
	run _sync_etc_nixos_flake_from_zanoni_system chise
	[ "$status" -eq 0 ]
	[[ "$output" != *"SUDO_CALLED"* ]]
}

@test "zanoni-system sync is skipped when /etc/nixos already matches" {
	_zanoni_system_flake_present() { return 0; }
	_etc_nixos_flake_matches_zanoni_system() { return 0; }
	_sudo() { echo "SUDO_CALLED"; }
	run _sync_etc_nixos_flake_from_zanoni_system chise
	[ "$status" -eq 0 ]
	[[ "$output" != *"SUDO_CALLED"* ]]
}

@test "zanoni-system sync installs /etc/nixos flake from zanoni-system when it differs" {
	_zanoni_system_flake_present() { return 0; }
	_etc_nixos_flake_matches_zanoni_system() { return 1; }
	_sudo() { echo "SUDO_CALLED $*"; }
	run _sync_etc_nixos_flake_from_zanoni_system chise
	[ "$status" -eq 0 ]
	[[ "$output" == *"SUDO_CALLED install -D -m 0644"* ]]
}

@test "nixos-rebuild is invoked with the rebuild-wrapper sentinel" {
	grep -q 'REBUILD_WRAPPER_SENTINEL.* nixos-rebuild switch' "$SCRIPT_UNDER_TEST"
	grep -q 'DOTFILES_REBUILD_WRAPPER=1' "$SCRIPT_UNDER_TEST"
}
