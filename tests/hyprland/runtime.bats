#!/usr/bin/env bats

setup() {
    if [ -z "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]; then
        skip "no Hyprland session running (HYPRLAND_INSTANCE_SIGNATURE unset)"
    fi
}

@test "hyprctl: responds to version command" {
    run hyprctl version
    [ "$status" -eq 0 ]
    [[ "$output" == *"Hyprland"* ]]
}

@test "hyprctl: version matches expected release" {
    run hyprctl version
    [[ "$output" == *"0.54"* ]]
}

@test "hyprctl: monitors configured" {
    result=$(hyprctl monitors -j)
    monitorCount=$(echo "$result" | jq length)
    [ "$monitorCount" -gt 0 ]
}

@test "hyprctl: active workspace exists" {
    result=$(hyprctl activeworkspace -j)
    echo "$result" | jq -e '.id' > /dev/null
}

@test "hyprctl: keybindings loaded" {
    result=$(hyprctl binds -j)
    bindCount=$(echo "$result" | jq length)
    [ "$bindCount" -gt 0 ]
}

@test "hyprctl: dwindle layout is active" {
    result=$(hyprctl activeworkspace -j)
    layout=$(echo "$result" | jq -r '.tiledLayout')
    [ "$layout" = "dwindle" ]
}

@test "hyprctl: no config errors" {
    run hyprctl configerrors -j
    [ "$status" -eq 0 ]
    errorCount=$(echo "$output" | jq '[.[] | select(. != "")] | length')
    [ "$errorCount" -eq 0 ]
}

@test "systemd: quickshell-bar service is active" {
    run systemctl --user is-active quickshell-bar.service
    [ "$output" = "active" ]
}

@test "systemd: mako service is active" {
    run systemctl --user is-active mako.service
    [ "$output" = "active" ]
}

@test "systemd: quickshell-switcher service is active" {
    run systemctl --user is-active quickshell-switcher.service
    [ "$output" = "active" ]
}
