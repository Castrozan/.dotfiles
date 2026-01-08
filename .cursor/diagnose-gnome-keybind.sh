#!/usr/bin/env bash
# Diagnostic script for GNOME keybinding issues

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
        --arg rid "diagnostic" \
        --arg hid "$hypothesis_id" \
        --argjson data "$data" \
        '{id: $id, timestamp: ($ts | tonumber), location: $loc, message: $msg, data: $data, sessionId: $sid, runId: $rid, hypothesisId: $hid}')
    echo "$log_entry" >> "$LOG_FILE"
    curl -s -X POST "$SERVER_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$log_entry" >/dev/null 2>&1 || true
}

# Hypothesis A: GNOME Shell has a conflicting keybinding for Super+d
check_shell_keybindings() {
    log "A" "diagnose-gnome-keybind.sh:check_shell_keybindings" "Checking GNOME Shell keybindings for Super+d conflict" \
        "$(dconf read /org/gnome/shell/keybindings/ 2>/dev/null | jq -R -s '{shell_keybindings: .}' || echo '{}')"
    
    # Check all shell keybindings
    local all_shell_bindings=$(dconf list /org/gnome/shell/keybindings/ 2>/dev/null)
    local super_d_found=false
    
    for key in $all_shell_bindings; do
        local binding=$(dconf read "/org/gnome/shell/keybindings/${key}" 2>/dev/null || echo "[]")
        if echo "$binding" | grep -q "Super.*d\|d.*Super" 2>/dev/null; then
            super_d_found=true
            log "A" "diagnose-gnome-keybind.sh:check_shell_keybindings" "Found conflicting shell keybinding" \
                "$(jq -n --arg key "$key" --arg binding "$binding" '{conflicting_key: $key, binding: $binding}')"
        fi
    done
    
    if [ "$super_d_found" = false ]; then
        log "A" "diagnose-gnome-keybind.sh:check_shell_keybindings" "No shell keybinding conflict found for Super+d" '{}'
    fi
}

# Hypothesis B: Custom keybinding not actually set in dconf
check_custom_keybinding() {
    log "B" "diagnose-gnome-keybind.sh:check_custom_keybinding" "Checking if custom5 keybinding is set in dconf" '{}'
    
    local custom5_path="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom5"
    local name=$(dconf read "${custom5_path}/name" 2>/dev/null || echo "NOT_SET")
    local binding=$(dconf read "${custom5_path}/binding" 2>/dev/null || echo "NOT_SET")
    local command=$(dconf read "${custom5_path}/command" 2>/dev/null || echo "NOT_SET")
    
    log "B" "diagnose-gnome-keybind.sh:check_custom_keybinding" "Custom5 keybinding values from dconf" \
        "$(jq -n --arg name "$name" --arg binding "$binding" --arg command "$command" \
        '{name: $name, binding: $binding, command: $command}')"
    
    # Check if custom5 is in the list
    local custom_list=$(dconf read /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings 2>/dev/null || echo "[]")
    local in_list=false
    if echo "$custom_list" | grep -q "custom5"; then
        in_list=true
    fi
    
    log "B" "diagnose-gnome-keybind.sh:check_custom_keybinding" "Custom5 in keybindings list" \
        "$(jq -n --argjson in_list "$in_list" '{in_list: $in_list, custom_list: $custom_list}')"
}

# Hypothesis C: Settings-daemon not running or plugin disabled
check_settings_daemon() {
    log "C" "diagnose-gnome-keybind.sh:check_settings_daemon" "Checking settings-daemon status" '{}'
    
    local daemon_running=$(pgrep -f "gnome-settings-daemon" >/dev/null && echo "true" || echo "false")
    local media_keys_enabled=$(dconf read /org/gnome/settings-daemon/plugins/media-keys/active 2>/dev/null || echo "true")
    
    log "C" "diagnose-gnome-keybind.sh:check_settings_daemon" "Settings-daemon status" \
        "$(jq -n --argjson running "$daemon_running" --arg enabled "$media_keys_enabled" \
        '{daemon_running: $running, media_keys_enabled: $enabled}')"
}

# Hypothesis D: Window manager keybinding conflict
check_wm_keybindings() {
    log "D" "diagnose-gnome-keybind.sh:check_wm_keybindings" "Checking window manager keybindings for Super+d conflict" '{}'
    
    local wm_bindings=$(dconf list /org/gnome/desktop/wm/keybindings/ 2>/dev/null)
    local super_d_found=false
    
    for key in $wm_bindings; do
        local binding=$(dconf read "/org/gnome/desktop/wm/keybindings/${key}" 2>/dev/null || echo "[]")
        if echo "$binding" | grep -q "Super.*d\|d.*Super" 2>/dev/null; then
            super_d_found=true
            log "D" "diagnose-gnome-keybind.sh:check_wm_keybindings" "Found conflicting WM keybinding" \
                "$(jq -n --arg key "$key" --arg binding "$binding" '{conflicting_key: $key, binding: $binding}')"
        fi
    done
    
    if [ "$super_d_found" = false ]; then
        log "D" "diagnose-gnome-keybind.sh:check_wm_keybindings" "No WM keybinding conflict found for Super+d" '{}'
    fi
}

# Hypothesis E: GNOME Shell extension intercepting the keybinding
check_extensions() {
    log "E" "diagnose-gnome-keybind.sh:check_extensions" "Checking enabled GNOME Shell extensions" '{}'
    
    local enabled_extensions=$(dconf read /org/gnome/shell/enabled-extensions 2>/dev/null || echo "[]")
    
    log "E" "diagnose-gnome-keybind.sh:check_extensions" "Enabled extensions list" \
        "$(jq -n --argjson extensions "$enabled_extensions" '{enabled_extensions: $extensions}')"
}

# Hypothesis F: Keybinding format or syntax issue
check_keybinding_format() {
    log "F" "diagnose-gnome-keybind.sh:check_keybinding_format" "Checking keybinding format" '{}'
    
    local binding=$(dconf read "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom5/binding" 2>/dev/null || echo "NOT_SET")
    local expected="'<Super>d'"
    
    log "F" "diagnose-gnome-keybind.sh:check_keybinding_format" "Keybinding format comparison" \
        "$(jq -n --arg actual "$binding" --arg expected "$expected" '{actual: $actual, expected: $expected, matches: ($actual == $expected)}')"
}

# Hypothesis G: Command path resolution issue
check_command_path() {
    log "G" "diagnose-gnome-keybind.sh:check_command_path" "Checking if daily-note command is in PATH" '{}'
    
    local command_path=$(which daily-note 2>/dev/null || echo "NOT_FOUND")
    local command_exists=$(command -v daily-note >/dev/null 2>&1 && echo "true" || echo "false")
    
    log "G" "diagnose-gnome-keybind.sh:check_command_path" "Command path resolution" \
        "$(jq -n --arg path "$command_path" --argjson exists "$command_exists" '{path: $path, exists: $exists}')"
    
    # Test if command actually works
    if [ "$command_exists" = "true" ]; then
        local test_output=$(daily-note 2>&1 &)
        sleep 0.5
        log "G" "diagnose-gnome-keybind.sh:check_command_path" "Command execution test" \
            "$(jq -n --arg output "$test_output" '{test_executed: true, output: $output}')"
    fi
}

# Main execution
main() {
    echo "Running GNOME keybinding diagnostics..."
    echo "Logs will be written to: $LOG_FILE"
    
    check_shell_keybindings
    check_custom_keybinding
    check_settings_daemon
    check_wm_keybindings
    check_extensions
    check_keybinding_format
    check_command_path
    
    echo "Diagnostics complete. Check $LOG_FILE for results."
}

main "$@"

