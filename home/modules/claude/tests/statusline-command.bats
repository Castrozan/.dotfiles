#!/usr/bin/env bats

load '../../../../tests/helpers/bash-script-assertions'

SCRIPT_UNDER_TEST="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)/../scripts/statusline-command.sh"

_strip_ansi_escape_codes() {
    sed 's/\x1b\[[0-9;]*m//g'
}

_run_statusline_with_json() {
    run bash -c "echo '$1' | bash '$SCRIPT_UNDER_TEST'"
}

_minimal_json_input() {
    echo '{"model":{"display_name":"Opus 4.6"},"cwd":"/tmp","session_id":"abcd1234-5678","context_window":{"used_percentage":10},"cost":{"total_cost_usd":0.05,"total_duration_ms":60000,"total_lines_added":0,"total_lines_removed":0}}'
}

_full_json_input() {
    local resets_at=$(($(date +%s) + 7200))
    echo '{"model":{"display_name":"Opus 4.6"},"cwd":"/tmp","session_id":"abcd1234-5678","session_name":"my-session","cost":{"total_cost_usd":0.42,"total_duration_ms":1823000,"total_lines_added":47,"total_lines_removed":12},"context_window":{"used_percentage":35.2},"rate_limits":{"five_hour":{"used_percentage":22.5,"resets_at":'"$resets_at"'}},"transcript_path":"/tmp/transcript.jsonl","agent":{"name":"jarvis"},"worktree":{"name":"feature-x","branch":"feat/x"},"vim":{"mode":"NORMAL"}}'
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "uses strict error handling" {
    assert_uses_strict_error_handling
}

@test "produces two lines of output" {
    _run_statusline_with_json "$(_minimal_json_input)"
    [ "$status" -eq 0 ]
    local line_count
    line_count=$(echo "$output" | wc -l)
    [ "$line_count" -eq 2 ]
}

@test "session id is truncated to 8 characters" {
    _run_statusline_with_json "$(_minimal_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" == *"abcd1234"* ]]
    [[ "$stripped" != *"abcd1234-5678"* ]]
}

@test "model name appears on line one" {
    _run_statusline_with_json "$(_minimal_json_input)"
    local line_one
    line_one=$(echo "$output" | head -1 | _strip_ansi_escape_codes)
    [[ "$line_one" == *"Opus 4.6"* ]]
}

@test "cost under 0.25 shows green formatting" {
    local json='{"model":{"display_name":"Test"},"cwd":"/tmp","session_id":"aaa","cost":{"total_cost_usd":0.10,"total_duration_ms":1000,"total_lines_added":0,"total_lines_removed":0},"context_window":{"used_percentage":5}}'
    _run_statusline_with_json "$json"
    local line_two
    line_two=$(echo "$output" | tail -1)
    [[ "$line_two" == *'\033[32m'* ]] || [[ "$line_two" == *$'\033[32m'* ]]
}

@test "cost over 1.00 shows red formatting" {
    local json='{"model":{"display_name":"Test"},"cwd":"/tmp","session_id":"aaa","cost":{"total_cost_usd":2.50,"total_duration_ms":1000,"total_lines_added":0,"total_lines_removed":0},"context_window":{"used_percentage":5}}'
    _run_statusline_with_json "$json"
    local line_two_stripped
    line_two_stripped=$(echo "$output" | tail -1 | _strip_ansi_escape_codes)
    [[ "$line_two_stripped" == *'$2.50'* ]]
}

@test "cost uses official total_cost_usd field" {
    local json='{"model":{"display_name":"Test"},"cwd":"/tmp","session_id":"aaa","cost":{"total_cost_usd":3.14,"total_duration_ms":1000,"total_lines_added":0,"total_lines_removed":0},"context_window":{"used_percentage":5}}'
    _run_statusline_with_json "$json"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" == *'$3.14'* ]]
}

@test "context bar at low usage shows magenta" {
    local json='{"model":{"display_name":"Test"},"cwd":"/tmp","session_id":"aaa","cost":{"total_cost_usd":0.01,"total_duration_ms":1000,"total_lines_added":0,"total_lines_removed":0},"context_window":{"used_percentage":15}}'
    _run_statusline_with_json "$json"
    local stripped
    stripped=$(echo "$output" | tail -1 | _strip_ansi_escape_codes)
    [[ "$stripped" == *"15%"* ]]
}

@test "context bar at high usage shows red" {
    local json='{"model":{"display_name":"Test"},"cwd":"/tmp","session_id":"aaa","cost":{"total_cost_usd":0.01,"total_duration_ms":1000,"total_lines_added":0,"total_lines_removed":0},"context_window":{"used_percentage":85}}'
    _run_statusline_with_json "$json"
    local stripped
    stripped=$(echo "$output" | tail -1 | _strip_ansi_escape_codes)
    [[ "$stripped" == *"85%"* ]]
}

@test "duration formats hours and minutes" {
    local json='{"model":{"display_name":"Test"},"cwd":"/tmp","session_id":"aaa","cost":{"total_cost_usd":0.01,"total_duration_ms":5400000,"total_lines_added":0,"total_lines_removed":0},"context_window":{"used_percentage":5}}'
    _run_statusline_with_json "$json"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" == *"session 1h30m"* ]]
}

@test "duration formats minutes and seconds when under one hour" {
    local json='{"model":{"display_name":"Test"},"cwd":"/tmp","session_id":"aaa","cost":{"total_cost_usd":0.01,"total_duration_ms":125000,"total_lines_added":0,"total_lines_removed":0},"context_window":{"used_percentage":5}}'
    _run_statusline_with_json "$json"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" == *"session 2m05s"* ]]
}

@test "duration formats seconds when under one minute" {
    local json='{"model":{"display_name":"Test"},"cwd":"/tmp","session_id":"aaa","cost":{"total_cost_usd":0.01,"total_duration_ms":45000,"total_lines_added":0,"total_lines_removed":0},"context_window":{"used_percentage":5}}'
    _run_statusline_with_json "$json"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" == *"session 45s"* ]]
}

@test "lines changed shows additions and removals" {
    local json='{"model":{"display_name":"Test"},"cwd":"/tmp","session_id":"aaa","cost":{"total_cost_usd":0.01,"total_duration_ms":1000,"total_lines_added":100,"total_lines_removed":25},"context_window":{"used_percentage":5}}'
    _run_statusline_with_json "$json"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" == *"+100"* ]]
    [[ "$stripped" == *"-25"* ]]
}

@test "lines changed hidden when both zero" {
    _run_statusline_with_json "$(_minimal_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" != *"+0"* ]]
    [[ "$stripped" != *"-0"* ]]
}

@test "rate limit shows percentage and resets in label" {
    _run_statusline_with_json "$(_full_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" == *"limit"* ]]
    [[ "$stripped" == *"22%"* ]]
    [[ "$stripped" == *"resets in"* ]]
}

@test "rate limit hidden when not present" {
    _run_statusline_with_json "$(_minimal_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" != *"limit"* ]]
    [[ "$stripped" != *"resets in"* ]]
}

@test "agent name shown only when present" {
    _run_statusline_with_json "$(_full_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" == *"jarvis"* ]]
}

@test "agent name hidden when not present" {
    _run_statusline_with_json "$(_minimal_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" != *"⚡"* ]]
}

@test "worktree shown with name and branch when present" {
    _run_statusline_with_json "$(_full_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" == *"feature-x"* ]]
    [[ "$stripped" == *"feat/x"* ]]
}

@test "worktree hidden when not present" {
    _run_statusline_with_json "$(_minimal_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" != *"🌿"* ]]
}

@test "vim mode shown only when present" {
    _run_statusline_with_json "$(_full_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" == *"NORMAL"* ]]
}

@test "vim mode hidden when not present" {
    _run_statusline_with_json "$(_minimal_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" != *"NORMAL"* ]]
    [[ "$stripped" != *"INSERT"* ]]
}

@test "session name shown when present" {
    _run_statusline_with_json "$(_full_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" == *"my-session"* ]]
}

@test "transcript shows log label with filename" {
    _run_statusline_with_json "$(_full_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" == *"log transcript.jsonl"* ]]
}

@test "transcript hidden when not present" {
    _run_statusline_with_json "$(_minimal_json_input)"
    local stripped
    stripped=$(echo "$output" | _strip_ansi_escape_codes)
    [[ "$stripped" != *"log "* ]]
}

@test "full output contains all segments on correct lines" {
    _run_statusline_with_json "$(_full_json_input)"
    local line_one line_two
    line_one=$(echo "$output" | head -1 | _strip_ansi_escape_codes)
    line_two=$(echo "$output" | tail -1 | _strip_ansi_escape_codes)

    [[ "$line_one" == *"abcd1234"* ]]
    [[ "$line_one" == *"jarvis"* ]]
    [[ "$line_one" == *"feature-x"* ]]
    [[ "$line_one" == *"my-session"* ]]
    [[ "$line_one" == *"Opus 4.6"* ]]

    [[ "$line_two" == *'$0.42'* ]]
    [[ "$line_two" == *"limit"* ]]
    [[ "$line_two" == *"session"* ]]
    [[ "$line_two" == *"+47"* ]]
    [[ "$line_two" == *"-12"* ]]
    [[ "$line_two" == *"35%"* ]]
    [[ "$line_two" == *"log transcript.jsonl"* ]]
}
