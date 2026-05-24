#!/usr/bin/env bats

load '../../../../../tests/helpers/bash-script-assertions'

SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)/../../scripts/statusline-command.sh"

_strip_ansi_escape_codes() {
    sed 's/\x1b\[[0-9;]*m//g'
}

_run_statusline_with_json() {
    run bash -c "echo '$1' | bash '$SCRIPT_UNDER_TEST'"
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
    git -C "$sandbox_repo_directory" config user.email test@example.com
    git -C "$sandbox_repo_directory" config user.name "Test"
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
