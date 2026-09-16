#!/usr/bin/env bats

readonly PULSE_AUDIO_DISCOVERY_QML="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../../../.." && pwd)/machine-configuration/desktop/desktop-environments/quickshell/bar/program-configuration/dashboard/services/audio/PulseAudioDiscovery.qml"

@test "pactl list sinks uses LC_ALL=C to prevent locale-dependent decimal separators in JSON" {
	grep -q 'LC_ALL=C.*pactl.*list.*sinks' "$PULSE_AUDIO_DISCOVERY_QML"
}

@test "pactl list sources uses LC_ALL=C to prevent locale-dependent decimal separators in JSON" {
	grep -q 'LC_ALL=C.*pactl.*list.*sources' "$PULSE_AUDIO_DISCOVERY_QML"
}

@test "pactl list cards uses LC_ALL=C to prevent locale-dependent decimal separators in JSON" {
	grep -q 'LC_ALL=C.*pactl.*list.*cards' "$PULSE_AUDIO_DISCOVERY_QML"
}
