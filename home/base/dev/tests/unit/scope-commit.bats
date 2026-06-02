#!/usr/bin/env bats

load '../../../../../tests/helpers/bash-script-assertions'

setup() {
	SCRIPT_UNDER_TEST="$DOTFILES_ROOT_DIRECTORY/.githooks/scope-commit.sh"
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
	cat "$commit_message_file"
}

@test "is executable" {
	assert_is_executable
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "prefixes subject with host scope for hosts/<host>/ changes" {
	run run_hook_after_staging_path_with_message "hosts/kira/default.nix" "fix: invert scroll"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "fix(kira): invert scroll" ]
}

@test "derives scope from home/hosts/darwin/<alias>.nix path" {
	run run_hook_after_staging_path_with_message "home/hosts/darwin/rin.nix" "feat: tweak"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "feat(rin): tweak" ]
}

@test "preserves the commit body below the rewritten subject" {
	run run_hook_after_staging_path_with_message "hosts/kira/default.nix" "fix: invert scroll\n\nbody line one\nbody line two"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "fix(kira): invert scroll" ]
	[ "${lines[1]}" = "body line one" ]
	[ "${lines[2]}" = "body line two" ]
}

@test "does not double-prefix an already-scoped subject" {
	run run_hook_after_staging_path_with_message "hosts/kira/default.nix" "fix(kira): invert scroll"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "fix(kira): invert scroll" ]
}

@test "leaves subject untouched when no scoped path is staged" {
	run run_hook_after_staging_path_with_message "README.md" "docs: update readme"
	[ "$status" -eq 0 ]
	[ "${lines[0]}" = "docs: update readme" ]
}
