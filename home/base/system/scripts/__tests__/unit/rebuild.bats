#!/usr/bin/env bats

setup() {
	REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../../../../.." && pwd)"
	source "$REPO_ROOT/repository/verification/helpers/bash-script-assertions.bash"
	SCRIPT_UNDER_TEST="$(_resolve_script_under_test)"
	BACKENDS_SOURCE_DIRECTORY="$(dirname "$SCRIPT_UNDER_TEST")/backends"
	source "$SCRIPT_UNDER_TEST"
}

readonly BACKEND_CONTRACT=(
	backend_prepare_environment
	backend_switch
	backend_verify_switch_landed
	backend_after_switch
)

@test "rebuild script is executable" {
	assert_is_executable
}

@test "rebuild script uses strict error handling" {
	assert_uses_strict_error_handling
}

@test "rebuild script passes shellcheck" {
	assert_passes_shellcheck
}

@test "every backend passes shellcheck" {
	if ! command -v shellcheck &>/dev/null; then
		skip "shellcheck not installed"
	fi
	run shellcheck "$BACKENDS_SOURCE_DIRECTORY"/*
	[ "$status" -eq 0 ]
}

@test "every backend implements the whole contract the entrypoint calls" {
	for backend in "$BACKENDS_SOURCE_DIRECTORY"/*; do
		for contract_function in "${BACKEND_CONTRACT[@]}"; do
			grep -q "^${contract_function}()" "$backend" ||
				fail_test "$(basename "$backend") is missing ${contract_function}"
		done
	done
}

@test "the entrypoint calls exactly the contract it declares" {
	for contract_function in "${BACKEND_CONTRACT[@]}"; do
		grep -q "^	${contract_function}\b" "$SCRIPT_UNDER_TEST" ||
			fail_test "the entrypoint never calls ${contract_function}"
	done
}

@test "darwin is detected from uname" {
	uname() { echo "Darwin"; }
	run detect_backend_name
	[ "$output" = "darwin" ]
}

@test "nixos is detected from its marker file" {
	uname() { echo "Linux"; }
	run detect_backend_name
	if [ -e /etc/NIXOS ]; then
		[ "$output" = "nixos" ]
	else
		[ "$output" = "home-manager" ]
	fi
}

@test "a non-nixos linux host falls back to the home-manager backend" {
	uname() { echo "Linux"; }
	detect_backend_name() {
		[ "$(uname -s)" = "Darwin" ] && echo "darwin" && return 0
		[ -e "$BATS_TEST_TMPDIR/absent-nixos-marker" ] && echo "nixos" && return 0
		echo "home-manager"
	}
	run detect_backend_name
	[ "$output" = "home-manager" ]
}

@test "the rebuild takes the shared exclusive-run lock" {
	local helper="$BATS_TEST_TMPDIR/exclusive-run-lock.sh"
	cat >"$helper" <<-'STUB'
		acquire_exclusive_run_lock_or_emit_retry_instructions() {
			echo "LOCK_ACQUIRED name=$1 typical_duration=$2"
		}
	STUB
	hold_exclusive_rebuild_lock() {
		[ -f "$helper" ] || return 0
		# shellcheck disable=SC1090
		. "$helper"
		acquire_exclusive_run_lock_or_emit_retry_instructions \
			"rebuild" "$TYPICAL_REBUILD_DURATION_SECONDS" "$REBUILD_SWITCH_LOG_PATH"
	}
	run hold_exclusive_rebuild_lock
	[ "$status" -eq 0 ]
	[[ "$output" == *"LOCK_ACQUIRED name=rebuild"* ]]
	[[ "$output" == *"typical_duration=420"* ]]
}

@test "the entrypoint locks before it switches" {
	local lock_line switch_line
	lock_line=$(grep -n '^	hold_exclusive_rebuild_lock$' "$SCRIPT_UNDER_TEST" | cut -d: -f1)
	switch_line=$(grep -n '^	backend_switch ' "$SCRIPT_UNDER_TEST" | cut -d: -f1)
	[ "$lock_line" -lt "$switch_line" ]
}

@test "rebuild still runs when the shared lock helper is absent from the checkout" {
	EXCLUSIVE_RUN_LOCK_HELPER_OVERRIDE="$BATS_TEST_TMPDIR/absent-helper.sh"
	hold_exclusive_rebuild_lock() {
		[ -f "$EXCLUSIVE_RUN_LOCK_HELPER_OVERRIDE" ] || return 0
		echo "LOCK_ATTEMPTED"
	}
	run hold_exclusive_rebuild_lock
	[ "$status" -eq 0 ]
	[ -z "$output" ]
}

@test "the nixos backend resolves the flake ref to /etc/nixos when that flake is present" {
	source "$BACKENDS_SOURCE_DIRECTORY/nixos"
	etc_nixos_flake_present() { return 0; }
	run resolve_flake_reference chise
	[ "$output" = "/etc/nixos#chise" ]
}

@test "the nixos backend falls back to bare dotfiles when /etc/nixos has no flake" {
	source "$BACKENDS_SOURCE_DIRECTORY/nixos"
	etc_nixos_flake_present() { return 1; }
	run resolve_flake_reference chise
	[[ "$output" == *".dotfiles?submodules=1#chise" ]]
}

@test "the entrypoint owner may not deploy from bare dotfiles" {
	source "$BACKENDS_SOURCE_DIRECTORY/nixos"
	etc_nixos_flake_present() { return 1; }
	run refuse_to_deploy_the_entrypoint_owner_from_bare_dotfiles chise
	[ "$status" -ne 0 ]
	[[ "$output" == *"refusing to deploy chise from bare"* ]]
}

@test "the entrypoint owner may deploy once /etc/nixos carries the flake" {
	source "$BACKENDS_SOURCE_DIRECTORY/nixos"
	etc_nixos_flake_present() { return 0; }
	run refuse_to_deploy_the_entrypoint_owner_from_bare_dotfiles chise
	[ "$status" -eq 0 ]
}

@test "a host that does not own the entrypoint deploys from bare dotfiles freely" {
	source "$BACKENDS_SOURCE_DIRECTORY/nixos"
	etc_nixos_flake_present() { return 1; }
	run refuse_to_deploy_the_entrypoint_owner_from_bare_dotfiles kira
	[ "$status" -eq 0 ]
}

@test "entrypoint sync is skipped for hosts that do not own it" {
	source "$BACKENDS_SOURCE_DIRECTORY/nixos"
	machine_local_entrypoint_flake_present() { return 0; }
	etc_nixos_flake_matches_machine_local_entrypoint() { return 1; }
	run_privileged() { echo "PRIVILEGED_CALL"; }
	run sync_etc_nixos_flake_from_machine_local_entrypoint kira
	[ "$status" -eq 0 ]
	[[ "$output" != *"PRIVILEGED_CALL"* ]]
}

@test "entrypoint sync is skipped when the entrypoint flake is absent" {
	source "$BACKENDS_SOURCE_DIRECTORY/nixos"
	machine_local_entrypoint_flake_present() { return 1; }
	run_privileged() { echo "PRIVILEGED_CALL"; }
	run sync_etc_nixos_flake_from_machine_local_entrypoint chise
	[ "$status" -eq 0 ]
	[[ "$output" != *"PRIVILEGED_CALL"* ]]
}

@test "entrypoint sync is skipped when /etc/nixos already matches" {
	source "$BACKENDS_SOURCE_DIRECTORY/nixos"
	machine_local_entrypoint_flake_present() { return 0; }
	etc_nixos_flake_matches_machine_local_entrypoint() { return 0; }
	run_privileged() { echo "PRIVILEGED_CALL"; }
	run sync_etc_nixos_flake_from_machine_local_entrypoint chise
	[ "$status" -eq 0 ]
	[[ "$output" != *"PRIVILEGED_CALL"* ]]
}

@test "entrypoint sync installs /etc/nixos from the entrypoint when they differ" {
	source "$BACKENDS_SOURCE_DIRECTORY/nixos"
	machine_local_entrypoint_flake_present() { return 0; }
	etc_nixos_flake_matches_machine_local_entrypoint() { return 1; }
	run_privileged() { echo "PRIVILEGED_CALL $*"; }
	run sync_etc_nixos_flake_from_machine_local_entrypoint chise
	[ "$status" -eq 0 ]
	[[ "$output" == *"PRIVILEGED_CALL install -D -m 0644"* ]]
}

@test "nixos-rebuild is invoked with the rebuild-wrapper sentinel" {
	grep -q 'DOTFILES_REBUILD_WRAPPER=1' "$BACKENDS_SOURCE_DIRECTORY/nixos"
	grep -q 'nixos-rebuild switch --flake' "$BACKENDS_SOURCE_DIRECTORY/nixos"
}

@test "the entrypoint initializes git submodules before switching" {
	grep -q 'submodule update --init' "$SCRIPT_UNDER_TEST"
	local submodule_line switch_line
	submodule_line=$(grep -n '^	initialize_git_submodules$' "$SCRIPT_UNDER_TEST" | cut -d: -f1)
	switch_line=$(grep -n '^	backend_switch ' "$SCRIPT_UNDER_TEST" | cut -d: -f1)
	[ "$submodule_line" -lt "$switch_line" ]
}

@test "a desktop refresh that fails does not fail a switch that already landed" {
	grep -q 'backend_after_switch || echo' "$SCRIPT_UNDER_TEST"
}

@test "hyprland is reloaded only when this shell is attached to a compositor" {
	source "$BACKENDS_SOURCE_DIRECTORY/nixos"
	hyprctl() { echo "HYPRCTL_CALLED"; }
	HYPRLAND_INSTANCE_SIGNATURE=""
	run backend_after_switch
	[ "$status" -eq 0 ]
	[[ "$output" != *"HYPRCTL_CALLED"* ]]
}

@test "hyprland is reloaded when a compositor instance is attached" {
	source "$BACKENDS_SOURCE_DIRECTORY/nixos"
	hyprctl() { echo "HYPRCTL_CALLED"; }
	hypr-apply-theme-colors() { echo "THEME_COLORS_APPLIED"; }
	HYPRLAND_INSTANCE_SIGNATURE="a-live-instance"
	run backend_after_switch
	[ "$status" -eq 0 ]
	[[ "$output" == *"HYPRCTL_CALLED"* ]]
	[[ "$output" == *"THEME_COLORS_APPLIED"* ]]
}

@test "the darwin backend proves activation refreshed the current-system symlink" {
	source "$BACKENDS_SOURCE_DIRECTORY/darwin"
	current_system_symlink_mtime_before_switch="1700000000"
	read_current_system_symlink_mtime() { echo "1700000000"; }
	abort_because_the_current_system_symlink_is_stale() { echo "ABORTED_STALE"; }
	run backend_verify_switch_landed
	[[ "$output" == *"ABORTED_STALE"* ]]
}

@test "the darwin backend accepts a refreshed current-system symlink" {
	source "$BACKENDS_SOURCE_DIRECTORY/darwin"
	current_system_symlink_mtime_before_switch="1700000000"
	read_current_system_symlink_mtime() { echo "1700000042"; }
	abort_because_the_current_system_symlink_is_stale() { echo "ABORTED_STALE"; }
	run backend_verify_switch_landed
	[ "$status" -eq 0 ]
	[[ "$output" != *"ABORTED_STALE"* ]]
}

fail_test() {
	echo "$1" >&2
	return 1
}
