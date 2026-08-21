#!/usr/bin/env bats

load '../../../../../repository/verification/helpers/bash-script-assertions'

SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)/../../settings/statusline/statusline-command.sh"

_strip_ansi_escape_codes() {
	sed 's/\x1b\[[0-9;]*m//g'
}

_run_statusline_with_json() {
	run bash -c "echo '$1' | bash '$SCRIPT_UNDER_TEST'"
}

_run_statusline_with_json_and_auto_compact_env() {
	local json_input="$1" auto_compact_window="$2" auto_compact_percentage="$3"
	run bash -c "echo '$json_input' | CLAUDE_CODE_AUTO_COMPACT_WINDOW='$auto_compact_window' CLAUDE_AUTOCOMPACT_PCT_OVERRIDE='$auto_compact_percentage' bash '$SCRIPT_UNDER_TEST'"
}

_run_statusline_with_json_without_auto_compact_env() {
	local json_input="$1"
	run bash -c "echo '$json_input' | env -u CLAUDE_CODE_AUTO_COMPACT_WINDOW -u CLAUDE_AUTOCOMPACT_PCT_OVERRIDE bash '$SCRIPT_UNDER_TEST'"
}

_run_statusline_with_servant_name_command() {
	local json_input="$1" servant_name_command_body="$2"
	local stub_bin_directory
	stub_bin_directory=$(mktemp -d)
	{
		echo '#!/usr/bin/env bash'
		echo "$servant_name_command_body"
	} >"$stub_bin_directory/servant-name"
	chmod +x "$stub_bin_directory/servant-name"
	run bash -c "echo '$json_input' | PATH='$stub_bin_directory:$PATH' bash '$SCRIPT_UNDER_TEST'"
	rm -rf "$stub_bin_directory"
}

_count_segment_separators() {
	printf "%s" "$1" | grep -o '│' | wc -l | tr -d ' '
}

_run_statusline_in_repository_directory() {
	local repository_directory="$1"
	_run_statusline_with_json '{"model":{"display_name":"Opus 4.7"},"cwd":"'"$repository_directory"'","session_id":"abc","context_window":{"used_percentage":5}}'
}

_configure_sandbox_repository_ignoring_ambient_git_hooks() {
	local sandbox_repository_directory="$1"
	local author_name="$2"
	local author_email="$3"
	git -C "$sandbox_repository_directory" config user.email "$author_email"
	git -C "$sandbox_repository_directory" config user.name "$author_name"
	git -C "$sandbox_repository_directory" config core.hooksPath /dev/null
}

_create_sandbox_repository_with_upstream() {
	local sandbox_root
	sandbox_root=$(mktemp -d)
	git init -q --bare -b main "$sandbox_root/remote.git"
	git -C "$sandbox_root" clone -q "$sandbox_root/remote.git" checkout 2>/dev/null
	_configure_sandbox_repository_ignoring_ambient_git_hooks \
		"$sandbox_root/checkout" "Test" test@example.com
	echo "first" >"$sandbox_root/checkout/file.txt"
	git -C "$sandbox_root/checkout" add file.txt
	git -C "$sandbox_root/checkout" commit -q -m "initial commit"
	git -C "$sandbox_root/checkout" push -q -u origin main
	printf "%s" "$sandbox_root"
}

_push_commit_to_upstream_behind_the_checkout() {
	local sandbox_root="$1"
	git -C "$sandbox_root" clone -q "$sandbox_root/remote.git" peer
	_configure_sandbox_repository_ignoring_ambient_git_hooks \
		"$sandbox_root/peer" "Peer" peer@example.com
	echo "peer" >>"$sandbox_root/peer/file.txt"
	git -C "$sandbox_root/peer" add file.txt
	git -C "$sandbox_root/peer" commit -q -m "peer commit"
	git -C "$sandbox_root/peer" push -q origin main
	rm -rf "$sandbox_root/peer"
}

_commits_behind_upstream_tracking_ref() {
	git -C "$1" rev-list --count 'HEAD..@{upstream}' 2>/dev/null || echo 0
}

_wait_for_upstream_tracking_ref_refresh() {
	local repository_directory="$1"
	local attempts_remaining=150
	while [ "$(_commits_behind_upstream_tracking_ref "$repository_directory")" -eq 0 ] && [ "$attempts_remaining" -gt 0 ]; do
		sleep 0.1
		attempts_remaining=$((attempts_remaining - 1))
	done
}

_upstream_fetch_marker_file_for_repository_directory() {
	# shellcheck disable=SC1090
	(source "$(dirname "$SCRIPT_UNDER_TEST")/statusline-command-git-segment.sh" && _upstream_fetch_marker_file_for_repository "$1")
}

_removed_git_cache_file_for_repository_directory() {
	local hashed_directory
	hashed_directory=$(echo "$1" | shasum | cut -d' ' -f1)
	printf "/tmp/claude-statusline-git-%s" "$hashed_directory"
}

_minimal_json_input() {
	echo '{"model":{"display_name":"Opus 4.7"},"cwd":"/tmp","session_id":"bb823787-e6ea-467c-b0ce-d90b8b92fc36","context_window":{"used_percentage":10}}'
}

_full_json_input() {
	local resets_at_epoch=$(($(date +%s) + 7500))
	echo '{"model":{"display_name":"Opus 4.7"},"cwd":"/tmp","session_id":"bb823787-e6ea-467c-b0ce-d90b8b92fc36","context_window":{"used_percentage":38},"rate_limits":{"five_hour":{"used_percentage":11,"resets_at":'"$resets_at_epoch"'}}}'
}

@test "passes shellcheck" {
	assert_passes_shellcheck
}

@test "uses strict error handling" {
	assert_uses_strict_error_handling
}

@test "renders exactly one line" {
	_run_statusline_with_json "$(_full_json_input)"
	[ "$status" -eq 0 ]
	local line_count
	line_count=$(echo "$output" | wc -l)
	[ "$line_count" -eq 1 ]
}

@test "model display name appears in output" {
	_run_statusline_with_json "$(_minimal_json_input)"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"Opus 4.7"* ]]
}

@test "full session id uuid is displayed" {
	_run_statusline_with_json "$(_minimal_json_input)"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"bb823787-e6ea-467c-b0ce-d90b8b92fc36"* ]]
}

@test "servant name appears next to the session id" {
	_run_statusline_with_servant_name_command "$(_minimal_json_input)" 'printf "%s\n" "Zhuge Liang"'
	[ "$status" -eq 0 ]
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"Zhuge Liang │ bb823787-e6ea-467c-b0ce-d90b8b92fc36"* ]]
}

@test "servant name is resolved from this session's own id" {
	_run_statusline_with_servant_name_command "$(_minimal_json_input)" 'printf "drawn-for-%s\n" "$1"'
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"drawn-for-bb823787-e6ea-467c-b0ce-d90b8b92fc36"* ]]
}

@test "servant segment hidden when the name cannot be resolved" {
	_run_statusline_with_servant_name_command "$(_minimal_json_input)" 'exit 1'
	[ "$status" -eq 0 ]
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[ "$(_count_segment_separators "$stripped")" -eq 2 ]
	[[ "$stripped" == *"bb823787-e6ea-467c-b0ce-d90b8b92fc36"* ]]
}

@test "servant segment hidden when the command names nobody" {
	_run_statusline_with_servant_name_command "$(_minimal_json_input)" 'exit 0'
	[ "$status" -eq 0 ]
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[ "$(_count_segment_separators "$stripped")" -eq 2 ]
}

@test "context window shows ctx label and rounded percentage" {
	_run_statusline_with_json "$(_minimal_json_input)"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"ctx 10%"* ]]
}

@test "context window at high usage shows percentage" {
	local json_input='{"model":{"display_name":"Opus 4.7"},"cwd":"/tmp","session_id":"abc","context_window":{"used_percentage":85}}'
	_run_statusline_with_json "$json_input"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"ctx 85%"* ]]
}

@test "context window percentage is computed against the auto-compact trigger" {
	local json_input='{"model":{"display_name":"Opus 4.7"},"cwd":"/tmp","session_id":"abc","context_window":{"used_percentage":18,"total_input_tokens":175000}}'
	_run_statusline_with_json_and_auto_compact_env "$json_input" 1000000 35
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"ctx 50%"* ]]
}

@test "context window percentage caps at 100 past the auto-compact trigger" {
	local json_input='{"model":{"display_name":"Opus 4.7"},"cwd":"/tmp","session_id":"abc","context_window":{"used_percentage":50,"total_input_tokens":500000}}'
	_run_statusline_with_json_and_auto_compact_env "$json_input" 1000000 35
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"ctx 100%"* ]]
}

@test "context window falls back to raw used_percentage without auto-compact env" {
	local json_input='{"model":{"display_name":"Opus 4.7"},"cwd":"/tmp","session_id":"abc","context_window":{"used_percentage":18,"total_input_tokens":175000}}'
	_run_statusline_with_json_without_auto_compact_env "$json_input"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"ctx 18%"* ]]
}

@test "rate limit shows lim label, percentage, and reset time" {
	_run_statusline_with_json "$(_full_json_input)"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"lim 11%"* ]]
	[[ "$stripped" == *"2h"* ]]
}

@test "rate limit segment hidden when rate_limits absent" {
	_run_statusline_with_json "$(_minimal_json_input)"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" != *"lim"* ]]
}

@test "context segment hidden when context_window absent" {
	local json_input='{"model":{"display_name":"Opus 4.7"},"cwd":"/tmp","session_id":"abc"}'
	_run_statusline_with_json "$json_input"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" != *"ctx"* ]]
}

@test "removed segments do not appear in output" {
	local resets_at_epoch=$(($(date +%s) + 7200))
	local json_input='{"model":{"display_name":"Opus 4.7"},"cwd":"/tmp","session_id":"abc","session_name":"my-session","cost":{"total_cost_usd":0.42,"total_duration_ms":1823000,"total_lines_added":47,"total_lines_removed":12},"context_window":{"used_percentage":35},"rate_limits":{"five_hour":{"used_percentage":22,"resets_at":'"$resets_at_epoch"'}},"transcript_path":"/tmp/transcript.jsonl","agent":{"name":"jarvis"},"worktree":{"name":"feature-x","branch":"feat/x"},"vim":{"mode":"NORMAL"}}'
	_run_statusline_with_json "$json_input"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" != *"NORMAL"* ]]
	[[ "$stripped" != *"jarvis"* ]]
	[[ "$stripped" != *"feature-x"* ]]
	[[ "$stripped" != *"my-session"* ]]
	[[ "$stripped" != *"transcript"* ]]
	[[ "$stripped" != *"0.42"* ]]
	[[ "$stripped" != *"+47"* ]]
	[[ "$stripped" != *"-12"* ]]
}

@test "segments are separated by the box-drawing pipe" {
	_run_statusline_with_json "$(_full_json_input)"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"│"* ]]
}

@test "git segment shows dirty marker when working tree is dirty" {
	local sandbox_repo_directory
	sandbox_repo_directory=$(mktemp -d)
	git -C "$sandbox_repo_directory" init -q -b main
	_configure_sandbox_repository_ignoring_ambient_git_hooks \
		"$sandbox_repo_directory" "Test" test@example.com
	echo "first" >"$sandbox_repo_directory/file.txt"
	git -C "$sandbox_repo_directory" add file.txt
	git -C "$sandbox_repo_directory" commit -q -m "initial commit"
	echo "second" >>"$sandbox_repo_directory/file.txt"
	local json_input
	json_input='{"model":{"display_name":"Opus 4.7"},"cwd":"'"$sandbox_repo_directory"'","session_id":"abc","context_window":{"used_percentage":5}}'
	_run_statusline_with_json "$json_input"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"main*"* ]]
	rm -rf "$sandbox_repo_directory"
}

@test "git segment shows ahead and behind counts against the upstream" {
	local sandbox_root
	sandbox_root=$(_create_sandbox_repository_with_upstream)
	_push_commit_to_upstream_behind_the_checkout "$sandbox_root"
	git -C "$sandbox_root/checkout" fetch -q origin main
	echo "local" >"$sandbox_root/checkout/local.txt"
	git -C "$sandbox_root/checkout" add local.txt
	git -C "$sandbox_root/checkout" commit -q -m "local commit"

	_run_statusline_in_repository_directory "$sandbox_root/checkout"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"main ↑1↓1"* ]]
	rm -rf "$sandbox_root"
}

@test "git segment refreshes a stale upstream tracking ref so the behind count appears" {
	local sandbox_root
	sandbox_root=$(_create_sandbox_repository_with_upstream)
	_push_commit_to_upstream_behind_the_checkout "$sandbox_root"
	[ "$(_commits_behind_upstream_tracking_ref "$sandbox_root/checkout")" -eq 0 ]

	_run_statusline_in_repository_directory "$sandbox_root/checkout"
	_wait_for_upstream_tracking_ref_refresh "$sandbox_root/checkout"

	_run_statusline_in_repository_directory "$sandbox_root/checkout"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"main ↓1"* ]]
	rm -rf "$sandbox_root"
}

@test "upstream fetch is rate limited by its marker file" {
	local sandbox_root
	sandbox_root=$(_create_sandbox_repository_with_upstream)
	local marker_file
	marker_file=$(_upstream_fetch_marker_file_for_repository_directory "$sandbox_root/checkout")
	rm -f "$marker_file"

	_run_statusline_in_repository_directory "$sandbox_root/checkout"
	[ -f "$marker_file" ]
	local first_attempt_epoch
	first_attempt_epoch=$(cat "$marker_file")

	sleep 1
	_run_statusline_in_repository_directory "$sandbox_root/checkout"
	[ "$(cat "$marker_file")" = "$first_attempt_epoch" ]

	rm -f "$marker_file"
	rm -rf "$sandbox_root"
}

@test "git segment does not block when the upstream remote is unreachable" {
	local sandbox_root
	sandbox_root=$(_create_sandbox_repository_with_upstream)
	git -C "$sandbox_root/checkout" remote set-url origin "https://10.255.255.1/unreachable.git"
	rm -f "$(_upstream_fetch_marker_file_for_repository_directory "$sandbox_root/checkout")"

	local started_at_epoch
	started_at_epoch=$(date +%s)
	_run_statusline_in_repository_directory "$sandbox_root/checkout"
	local elapsed_seconds=$(($(date +%s) - started_at_epoch))
	[ "$status" -eq 0 ]
	[ "$elapsed_seconds" -lt 5 ]

	rm -f "$(_upstream_fetch_marker_file_for_repository_directory "$sandbox_root/checkout")"
	rm -rf "$sandbox_root"
}

@test "git segment writes no cached copy of itself for a large repository" {
	local sandbox_root
	sandbox_root=$(_create_sandbox_repository_with_upstream)
	local file_index
	for file_index in $(seq 1 500); do
		: >"$sandbox_root/checkout/file-$file_index.txt"
	done
	git -C "$sandbox_root/checkout" add .
	git -C "$sandbox_root/checkout" commit -q -m "many tracked files"

	local removed_cache_file
	removed_cache_file=$(_removed_git_cache_file_for_repository_directory "$sandbox_root/checkout")
	rm -f "$removed_cache_file"

	_run_statusline_in_repository_directory "$sandbox_root/checkout"
	[ ! -f "$removed_cache_file" ]

	rm -f "$(_upstream_fetch_marker_file_for_repository_directory "$sandbox_root/checkout")"
	rm -rf "$sandbox_root"
}

@test "git segment reflects a new commit on the very next render" {
	local sandbox_root
	sandbox_root=$(_create_sandbox_repository_with_upstream)
	echo "one" >"$sandbox_root/checkout/one.txt"
	git -C "$sandbox_root/checkout" add one.txt
	git -C "$sandbox_root/checkout" commit -q -m "first local commit"

	_run_statusline_in_repository_directory "$sandbox_root/checkout"
	local stripped
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"main ↑1"* ]]

	echo "two" >"$sandbox_root/checkout/two.txt"
	git -C "$sandbox_root/checkout" add two.txt
	git -C "$sandbox_root/checkout" commit -q -m "second local commit"

	_run_statusline_in_repository_directory "$sandbox_root/checkout"
	stripped=$(echo "$output" | _strip_ansi_escape_codes)
	[[ "$stripped" == *"main ↑2"* ]]

	rm -f "$(_upstream_fetch_marker_file_for_repository_directory "$sandbox_root/checkout")"
	rm -rf "$sandbox_root"
}
