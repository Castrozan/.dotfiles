#!/usr/bin/env bash
# Wrapper script for daily-note with logging to diagnose keybinding issues

LOG_FILE="/home/lucas.zanoni/.dotfiles/.cursor/debug.log"
SERVER_ENDPOINT="http://127.0.0.1:7243/ingest/a03a8c8e-d2d3-42fd-a274-4275b56db24a"

log() {
    local hypothesis_id=$1
    local location=$2
    local message=$3
    local data=$4
    local timestamp=$(date +%s%3N)
    local log_entry=$(jq -n \
        --arg id "log_${timestamp}_$$" \
        --arg ts "$timestamp" \
        --arg loc "$location" \
        --arg msg "$message" \
        --arg sid "debug-session" \
        --arg rid "keybind-trigger" \
        --arg hid "$hypothesis_id" \
        --argjson data "$data" \
        '{id: $id, timestamp: ($ts | tonumber), location: $loc, message: $msg, data: $data, sessionId: $sid, runId: $rid, hypothesisId: $hid}')
    echo "$log_entry" >> "$LOG_FILE"
    curl -s -X POST "$SERVER_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$log_entry" >/dev/null 2>&1 || true
}

# Log that the wrapper was called
log "K" "daily-note-wrapper.sh:main" "Wrapper script called - keybinding triggered!" \
    "$(jq -n --arg pid "$$" --arg user "$USER" --arg pwd "$PWD" '{pid: $pid, user: $user, pwd: $pwd, env_editor: $ENV.EDITOR}')"

# Check if daily-note exists
if ! command -v daily-note >/dev/null 2>&1; then
    log "K" "daily-note-wrapper.sh:main" "ERROR: daily-note command not found in PATH" \
        "$(jq -n --arg path "$PATH" '{path: $path}')"
    exit 1
fi

# Execute the actual command
log "K" "daily-note-wrapper.sh:main" "Executing daily-note command" '{}'
exec daily-note "$@"

