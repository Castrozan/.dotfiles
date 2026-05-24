#!/usr/bin/env bats

readonly AUDIO_SERVICE_QML="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../../../.." && pwd)/.config/quickshell/bar/dashboard/services/AudioService.qml"

@test "pactl list sinks uses LC_ALL=C to prevent locale-dependent decimal separators in JSON" {
    grep -q 'LC_ALL=C.*pactl.*list.*sinks' "$AUDIO_SERVICE_QML"
}

@test "pactl list sources uses LC_ALL=C to prevent locale-dependent decimal separators in JSON" {
    grep -q 'LC_ALL=C.*pactl.*list.*sources' "$AUDIO_SERVICE_QML"
}

@test "pactl list cards uses LC_ALL=C to prevent locale-dependent decimal separators in JSON" {
    grep -q 'LC_ALL=C.*pactl.*list.*cards' "$AUDIO_SERVICE_QML"
}
