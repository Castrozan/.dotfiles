#!/usr/bin/env bats

setup() {
    PINCHTAB_BIN="$(command -v pinchtab 2>/dev/null || true)"
    if [ -z "$PINCHTAB_BIN" ]; then
        skip "pinchtab not in PATH (requires home-manager profile)"
    fi
}

@test "pinchtab binary exists in PATH" {
    [ -x "$PINCHTAB_BIN" ]
}

@test "pinchtab wrapper sets BRIDGE_HEADLESS default to true" {
    run grep -q 'BRIDGE_HEADLESS' "$PINCHTAB_BIN"
    [ "$status" -eq 0 ]
}

@test "pinchtab wrapper sets CHROME_BINARY from chromium" {
    run grep -q 'CHROME_BINARY' "$PINCHTAB_BIN"
    [ "$status" -eq 0 ]
}

@test "pinchtab wrapper configures wayland display detection" {
    run grep -q 'WAYLAND_DISPLAY' "$PINCHTAB_BIN"
    [ "$status" -eq 0 ]
}

@test "pinchtab wrapper sets persistent profile path" {
    run grep -q 'BRIDGE_PROFILE' "$PINCHTAB_BIN"
    [ "$status" -eq 0 ]
}

@test "pinchtab wrapper uses strict error handling" {
    run head -5 "$PINCHTAB_BIN"
    [[ "$output" == *"set -euo pipefail"* ]]
}

@test "pinchtab-navigate-and-snapshot binary exists in PATH" {
    run command -v pinchtab-navigate-and-snapshot
    [ "$status" -eq 0 ]
}

@test "pinchtab-navigate-and-snapshot uses strict error handling" {
    local script_bin
    script_bin="$(command -v pinchtab-navigate-and-snapshot)"
    run head -5 "$script_bin"
    [[ "$output" == *"set -Eeuo pipefail"* ]]
}

@test "pinchtab-navigate-and-snapshot calls navigate and snapshot endpoints" {
    local script_bin
    script_bin="$(command -v pinchtab-navigate-and-snapshot)"
    run grep -q '/navigate' "$script_bin"
    [ "$status" -eq 0 ]
    run grep -q '/snapshot' "$script_bin"
    [ "$status" -eq 0 ]
}

@test "pinchtab-act-and-snapshot binary exists in PATH" {
    run command -v pinchtab-act-and-snapshot
    [ "$status" -eq 0 ]
}

@test "pinchtab-act-and-snapshot uses strict error handling" {
    local script_bin
    script_bin="$(command -v pinchtab-act-and-snapshot)"
    run head -5 "$script_bin"
    [[ "$output" == *"set -Eeuo pipefail"* ]]
}

@test "pinchtab-act-and-snapshot calls action and snapshot endpoints" {
    local script_bin
    script_bin="$(command -v pinchtab-act-and-snapshot)"
    run grep -q '/action' "$script_bin"
    [ "$status" -eq 0 ]
    run grep -q '/snapshot' "$script_bin"
    [ "$status" -eq 0 ]
}

@test "pinchtab-act-and-snapshot defaults to diff snapshot" {
    local script_bin
    script_bin="$(command -v pinchtab-act-and-snapshot)"
    run grep -q 'diff=true' "$script_bin"
    [ "$status" -eq 0 ]
}

@test "pinchtab-fill-form binary exists in PATH" {
    run command -v pinchtab-fill-form
    [ "$status" -eq 0 ]
}

@test "pinchtab-fill-form uses strict error handling" {
    local script_bin
    script_bin="$(command -v pinchtab-fill-form)"
    run head -5 "$script_bin"
    [[ "$output" == *"set -Eeuo pipefail"* ]]
}

@test "pinchtab-fill-form calls evaluate endpoint" {
    local script_bin
    script_bin="$(command -v pinchtab-fill-form)"
    run grep -q '/evaluate' "$script_bin"
    [ "$status" -eq 0 ]
}

@test "pinchtab-fill-form handles native value setter for React compatibility" {
    local script_bin
    script_bin="$(command -v pinchtab-fill-form)"
    run grep -q 'nativeValueSetter\|getOwnPropertyDescriptor' "$script_bin"
    [ "$status" -eq 0 ]
}

@test "pinchtab-fill-form detects textarea elements for correct prototype" {
    local script_bin
    script_bin="$(command -v pinchtab-fill-form)"
    run grep -q 'HTMLTextAreaElement' "$script_bin"
    [ "$status" -eq 0 ]
}

@test "pinchtab-fill-form handles checkbox and radio via element click" {
    local script_bin
    script_bin="$(command -v pinchtab-fill-form)"
    run grep -q 'el.click()' "$script_bin"
    [ "$status" -eq 0 ]
}

@test "pinchtab-fill-form processes all fields in single evaluate call" {
    local script_bin
    script_bin="$(command -v pinchtab-fill-form)"
    local evaluate_count
    evaluate_count=$(grep -c '/evaluate' "$script_bin")
    [ "$evaluate_count" -eq 1 ]
}
