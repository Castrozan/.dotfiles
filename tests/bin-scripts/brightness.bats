#!/usr/bin/env bats

load '../helpers/bash-script-assertions'

@test "is executable" {
    assert_is_executable
}

@test "passes shellcheck" {
    assert_passes_shellcheck
}

@test "uses strict error handling" {
    assert_uses_strict_error_handling
}

@test "uses brightnessctl for control" {
    assert_script_source_matches "brightnessctl"
}

@test "sends mako-compatible notifications" {
    assert_script_source_matches_all \
        "x-canonical-private-synchronous" \
        "int:value:" \
        "notify-send"
}

@test "supports all required cli flags" {
    assert_script_source_matches_all \
        "\-\-inc)" \
        "\-\-dec)" \
        "\-\-inc-precise)" \
        "\-\-dec-precise)" \
        "\-\-get)"
}

@test "follows canonical script pattern with main entry point" {
    assert_script_source_matches '^main\(\)'
    assert_script_source_matches '^main "\$@"'
}

@test "uses readonly constants" {
    assert_script_source_matches_all \
        "readonly BRIGHTNESS_STEP_NORMAL" \
        "readonly BRIGHTNESS_STEP_PRECISE" \
        "readonly NOTIFICATION_TIMEOUT"
}

@test "private helpers prefixed with underscore" {
    assert_script_source_matches_all \
        "_change_brightness" \
        "_get_brightness_percentage" \
        "_get_brightness_icon_name"
}
