#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

setup() {
	SCRIPT_UNDER_TEST="$DOTFILES_ROOT_DIRECTORY/repository/git-hooks/scope-commit.sh"
	export SCRIPT_UNDER_TEST
	temporary_repository="$(mktemp -d)"
	git -C "$temporary_repository" init -q
	git -C "$temporary_repository" config user.email test@example.com
	git -C "$temporary_repository" config user.name "test"
}

teardown() {
	rm -rf "$temporary_repository"
}

run_hook_after_staging_path_with_message() {
	local staged_relative_path="$1"
	local commit_message="$2"
	mkdir -p "$temporary_repository/$(dirname "$staged_relative_path")"
	printf 'content\n' >"$temporary_repository/$staged_relative_path"
	git -C "$temporary_repository" add "$staged_relative_path"
	local commit_message_file="$temporary_repository/COMMIT_EDITMSG"
	printf '%b' "$commit_message" >"$commit_message_file"
	(cd "$temporary_repository" && "$SCRIPT_UNDER_TEST" "$commit_message_file")
	local hook_status=$?
	cat "$commit_message_file"
	return "$hook_status"
}

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "prefixes subject with machine scope for system module changes" {
	run run_hook_after_staging_path_with_message "machine-configuration/machines/kira/system/default.nix" "fix: invert scroll"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "fix(kira): invert scroll" ]
}

@test "derives scope from machine home entry point changes" {
	run run_hook_after_staging_path_with_message "machine-configuration/machines/rin/home.nix" "feat: tweak"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "feat(rin): tweak" ]
}

@test "derives scope from machine home module changes" {
	run run_hook_after_staging_path_with_message "machine-configuration/machines/chise/home/git.nix" "fix: update identity"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "fix(chise): update identity" ]
}

@test "derives scope from shared darwin machine composition changes" {
	run run_hook_after_staging_path_with_message "machine-configuration/machines/shared-darwin-system-nix-darwin.nix" "fix: invert scroll"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "fix(shared-darwin): invert scroll" ]
}

@test "derives scope from repository git hook changes" {
	run run_hook_after_staging_path_with_message "repository/git-hooks/scope-commit.sh" "fix: invert scroll"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "fix(git-hooks): invert scroll" ]
}

@test "rejects a subject without a conventional type on a scoped path" {
	run run_hook_after_staging_path_with_message "machine-configuration/machines/kira/system/default.nix" "invert scroll"
	[ "$status" -eq 1 ]
}

@test "rejects a subject without a conventional type on an unscoped path" {
	run run_hook_after_staging_path_with_message "README.md" "invert scroll"
	[ "$status" -eq 1 ]
}

@test "passes through git-generated merge subjects" {
	run run_hook_after_staging_path_with_message "machine-configuration/machines/kira/system/default.nix" "Merge branch 'main'"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "Merge branch 'main'" ]
}

@test "preserves the commit body below the rewritten subject" {
	run run_hook_after_staging_path_with_message "machine-configuration/machines/kira/system/default.nix" "fix: invert scroll\n\nbody line one\nbody line two"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "fix(kira): invert scroll" ]
	[ "${lines[1]}" = "body line one" ]
	[ "${lines[2]}" = "body line two" ]
}

@test "does not double-prefix an already-scoped subject" {
	run run_hook_after_staging_path_with_message "machine-configuration/machines/kira/system/default.nix" "fix(kira): invert scroll"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "fix(kira): invert scroll" ]
}

@test "leaves subject untouched when no scoped path is staged" {
	run run_hook_after_staging_path_with_message "README.md" "docs: update readme"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "docs: update readme" ]
}
