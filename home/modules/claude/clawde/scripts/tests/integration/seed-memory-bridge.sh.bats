#!/usr/bin/env bats

load '../../../../../../../tests/helpers/bash-script-assertions'

setup() {
	TEST_TEMPORARY_ROOT=$(mktemp -d)
	export HOME="$TEST_TEMPORARY_ROOT/home"
	mkdir -p "$HOME"
	AGENT_WORKSPACE_PATH="$TEST_TEMPORARY_ROOT/workspace"
	mkdir -p "$AGENT_WORKSPACE_PATH"
	ENCODED_PROJECT_NAME="${AGENT_WORKSPACE_PATH//[\/.]/-}"
	HARNESS_MEMORY_DIRECTORY="$HOME/.claude/projects/$ENCODED_PROJECT_NAME/memory"
}

teardown() {
	rm -rf "$TEST_TEMPORARY_ROOT"
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "uses strict error handling" {
	assert_uses_strict_error_handling
}

@test "errors when called without workspace argument" {
	run_script_under_test
	[ "$status" -ne 0 ]
}

@test "creates canonical memory directory at workspace" {
	run_script_under_test "$AGENT_WORKSPACE_PATH"
	[ "$status" -eq 0 ]
	[ -d "$AGENT_WORKSPACE_PATH/memory" ]
}

@test "seeds MEMORY.md with index header on fresh workspace" {
	run_script_under_test "$AGENT_WORKSPACE_PATH"
	[ -f "$AGENT_WORKSPACE_PATH/memory/MEMORY.md" ]
	run grep -q "# Memory index" "$AGENT_WORKSPACE_PATH/memory/MEMORY.md"
	[ "$status" -eq 0 ]
}

@test "preserves existing MEMORY.md content on re-run" {
	mkdir -p "$AGENT_WORKSPACE_PATH/memory"
	echo "preexisting custom content" >"$AGENT_WORKSPACE_PATH/memory/MEMORY.md"
	run_script_under_test "$AGENT_WORKSPACE_PATH"
	run grep -q "preexisting custom content" "$AGENT_WORKSPACE_PATH/memory/MEMORY.md"
	[ "$status" -eq 0 ]
}

@test "creates harness symlink pointing to canonical directory" {
	run_script_under_test "$AGENT_WORKSPACE_PATH"
	[ -L "$HARNESS_MEMORY_DIRECTORY" ]
	current_target=$(readlink "$HARNESS_MEMORY_DIRECTORY")
	[ "$current_target" = "$AGENT_WORKSPACE_PATH/memory" ]
}

@test "is idempotent across repeated runs" {
	run_script_under_test "$AGENT_WORKSPACE_PATH"
	[ "$status" -eq 0 ]
	run_script_under_test "$AGENT_WORKSPACE_PATH"
	[ "$status" -eq 0 ]
	[ -L "$HARNESS_MEMORY_DIRECTORY" ]
}

@test "replaces empty harness directory with symlink" {
	mkdir -p "$HARNESS_MEMORY_DIRECTORY"
	run_script_under_test "$AGENT_WORKSPACE_PATH"
	[ "$status" -eq 0 ]
	[ -L "$HARNESS_MEMORY_DIRECTORY" ]
}

@test "warns and skips when harness directory has content" {
	mkdir -p "$HARNESS_MEMORY_DIRECTORY"
	echo "preexisting harness fact" >"$HARNESS_MEMORY_DIRECTORY/legacy-memory.md"
	combined_output=$("$(_resolve_script_under_test)" "$AGENT_WORKSPACE_PATH" 2>&1)
	[ ! -L "$HARNESS_MEMORY_DIRECTORY" ]
	[ -d "$HARNESS_MEMORY_DIRECTORY" ]
	[ -f "$HARNESS_MEMORY_DIRECTORY/legacy-memory.md" ]
	[[ "$combined_output" == *"manual migration required"* ]]
}

@test "replaces wrong-target symlink with correct one" {
	mkdir -p "$(dirname "$HARNESS_MEMORY_DIRECTORY")"
	ln -s "$TEST_TEMPORARY_ROOT/somewhere-else" "$HARNESS_MEMORY_DIRECTORY"
	run_script_under_test "$AGENT_WORKSPACE_PATH"
	[ "$status" -eq 0 ]
	[ -L "$HARNESS_MEMORY_DIRECTORY" ]
	current_target=$(readlink "$HARNESS_MEMORY_DIRECTORY")
	[ "$current_target" = "$AGENT_WORKSPACE_PATH/memory" ]
}
