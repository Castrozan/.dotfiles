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

@test "uses pactl instead of pamixer" {
    assert_script_source_matches "pactl"
    run grep -c "pamixer" "$(_resolve_script_under_test)"
    [ "$output" = "0" ]
}

@test "targets running sink before default" {
    assert_script_source_matches 'RUNNING.*print'
    assert_script_source_matches '@DEFAULT_SINK@'
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
        "\-\-toggle)" \
        "\-\-toggle-mic)" \
        "\-\-mic-inc)" \
        "\-\-mic-dec)" \
        "\-\-get)" \
        "\-\-get-icon)"
}

@test "follows canonical script pattern with main entry point" {
    assert_script_source_matches '^main\(\)'
    assert_script_source_matches '^main "\$@"'
}

@test "uses readonly constants" {
    assert_script_source_matches_all \
        "readonly VOLUME_STEP_NORMAL" \
        "readonly VOLUME_STEP_PRECISE" \
        "readonly NOTIFICATION_TIMEOUT"
}

@test "private helpers prefixed with underscore" {
    assert_script_source_matches_all \
        "_find_active_sink_name_or_default" \
        "_get_volume_for_active_sink" \
        "_send_notification"
}
