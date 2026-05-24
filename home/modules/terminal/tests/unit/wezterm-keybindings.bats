#!/usr/bin/env bats

readonly WEZTERM_CONFIG="$BATS_TEST_DIRNAME/../../../../.config/wezterm/wezterm.lua"

@test "shift+enter sends CSI-u sequence not raw newline" {
    run grep "key = 'Enter'.*SHIFT" "$WEZTERM_CONFIG"
    [[ "$output" == *"\\x1b[13;2u"* ]]
    [[ "$output" != *"SendString('\\n')"* ]]
}

@test "ctrl+enter sends CSI-u sequence" {
    run grep "key = 'Enter'.*CTRL" "$WEZTERM_CONFIG"
    [[ "$output" == *"\\x1b[13;5u"* ]]
}

@test "alt+enter sends CSI-u sequence" {
    run grep "key = 'Enter'.*ALT" "$WEZTERM_CONFIG"
    [[ "$output" == *"\\x1b[13;3u"* ]]
}

@test "csi-u key encoding is enabled" {
    run grep "enable_csi_u_key_encoding" "$WEZTERM_CONFIG"
    [[ "$output" == *"true"* ]]
}
