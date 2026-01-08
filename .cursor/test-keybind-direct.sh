#!/usr/bin/env bash
# Direct test script to verify keybinding works

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
        --arg rid "direct-test" \
        --arg hid "$hypothesis_id" \
        --argjson data "$data" \
        '{id: $id, timestamp: ($ts | tonumber), location: $loc, message: $msg, data: $data, sessionId: $sid, runId: $rid, hypothesisId: $hid}')
    echo "$log_entry" >> "$LOG_FILE"
    curl -s -X POST "$SERVER_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$log_entry" >/dev/null 2>&1 || true
}

# Test if we can manually trigger the command
log "L" "test-keybind-direct.sh:main" "Testing direct command execution" '{}'

# Check current keybinding state
binding=$(gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom5/ binding 2>/dev/null)
command=$(gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom5/ command 2>/dev/null)

log "L" "test-keybind-direct.sh:main" "Current keybinding state" \
    "$(jq -n --arg binding "$binding" --arg command "$command" '{binding: $binding, command: $command}')"

# Try to manually execute the command to see if it works
log "L" "test-keybind-direct.sh:main" "Attempting to execute command directly" '{}'
bash -c '/home/lucas.zanoni/.dotfiles/.cursor/daily-note-wrapper.sh' &
sleep 1

log "L" "test-keybind-direct.sh:main" "Direct execution test complete" '{}'

echo "Test complete. Check logs for results."
echo "Current binding: $binding"
echo "Current command: $command"

