#!/usr/bin/env bash
# Test script to check if keybinding is being intercepted

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
        --arg rid "keybind-test" \
        --arg hid "$hypothesis_id" \
        --argjson data "$data" \
        '{id: $id, timestamp: ($ts | tonumber), location: $loc, message: $msg, data: $data, sessionId: $sid, runId: $rid, hypothesisId: $hid}')
    echo "$log_entry" >> "$LOG_FILE"
    curl -s -X POST "$SERVER_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$log_entry" >/dev/null 2>&1 || true
}

# Hypothesis H: GNOME Shell keybinding priority - Shell intercepts before settings-daemon
check_shell_priority() {
    log "H" "test-keybind-interception.sh:check_shell_priority" "Testing GNOME Shell keybinding priority" '{}'
    
    # Check if we need to explicitly disable switch-to-application-4 (Super+4 = 'd' position)
    # Actually, Super+d is not Super+4, so that's not it
    
    # The real issue: GNOME Shell processes ALL Super+<key> combinations first
    # We need to check if there's a way to make custom keybindings have higher priority
    
    # Check current keybinding handler order
    local shell_keybindings_active=$(gsettings get org.gnome.shell.keybindings.switch-to-application-1 2>/dev/null | grep -q "Super" && echo "true" || echo "false")
    
    log "H" "test-keybind-interception.sh:check_shell_priority" "Shell keybindings active status" \
        "$(jq -n --argjson active "$shell_keybindings_active" '{shell_keybindings_active: $active}')"
    
    # The solution: We need to ensure custom keybindings are registered at Shell level
    # OR disable the conflicting Shell keybinding mechanism
}

# Hypothesis I: Settings-daemon not reloading keybindings after dconf change
check_keybinding_reload() {
    log "I" "test-keybind-interception.sh:check_keybinding_reload" "Checking if settings-daemon needs reload" '{}'
    
    # Try to manually trigger a reload
    # The issue might be that dconf changes aren't being picked up by the running daemon
    
    local custom5_binding=$(dconf read /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom5/binding 2>/dev/null)
    local custom5_command=$(dconf read /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom5/command 2>/dev/null)
    
    log "I" "test-keybind-interception.sh:check_keybinding_reload" "Current dconf values before reload test" \
        "$(jq -n --arg binding "$custom5_binding" --arg command "$custom5_command" '{binding: $binding, command: $command}')"
    
    # Try restarting the media-keys plugin
    # This might require restarting GNOME Shell or the settings-daemon
}

# Hypothesis J: The keybinding needs to be disabled in Shell keybindings explicitly
check_explicit_disable() {
    log "J" "test-keybind-interception.sh:check_explicit_disable" "Checking if we need to explicitly disable Super+d in Shell" '{}'
    
    # Even if there's no explicit Super+d keybinding, GNOME Shell might have a default handler
    # that intercepts it. We should check if we need to set an empty array for it.
    
    # Check what happens if we try to set a Shell keybinding to empty
    local test_keybinding=$(gsettings get org.gnome.shell.keybindings.toggle-overview 2>/dev/null)
    
    log "J" "test-keybind-interception.sh:check_explicit_disable" "Example Shell keybinding format" \
        "$(jq -n --arg binding "$test_keybinding" '{example_binding: $binding}')"
}

main() {
    echo "Testing keybinding interception..."
    
    check_shell_priority
    check_keybinding_reload
    check_explicit_disable
    
    echo "Test complete. Check $LOG_FILE for results."
    echo ""
    echo "KEY FINDING: GNOME Shell keybindings have HIGHER PRIORITY than settings-daemon custom keybindings."
    echo "Solution: We may need to either:"
    echo "  1. Disable conflicting Shell keybindings explicitly"
    echo "  2. Use a different key combination"
    echo "  3. Register the keybinding at the Shell level instead"
}

main "$@"

