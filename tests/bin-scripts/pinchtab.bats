#!/usr/bin/env bats

setup() {
    PINCHTAB_BIN="$(command -v pinchtab)"
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
