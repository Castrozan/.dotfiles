import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/dashboard/services/audio/AudioDeviceData.js" as AudioDeviceData

Item {
    TestCase {
        name: "AudioServiceExtractVolumePercent"

        function test_extracts_volume_from_single_channel() {
            var volume = {
                "front-left": {
                    value_percent: "75%"
                }
            };
            compare(AudioDeviceData.extractVolumePercent(volume), 75);
        }

        function test_extracts_volume_from_multi_channel() {
            var volume = {
                "front-left": {
                    value_percent: "50%"
                },
                "front-right": {
                    value_percent: "60%"
                }
            };
            compare(AudioDeviceData.extractVolumePercent(volume), 50);
        }

        function test_returns_zero_for_null_volume() {
            compare(AudioDeviceData.extractVolumePercent(null), 0);
        }

        function test_returns_zero_for_undefined_volume() {
            compare(AudioDeviceData.extractVolumePercent(undefined), 0);
        }

        function test_returns_zero_for_empty_volume_object() {
            compare(AudioDeviceData.extractVolumePercent({}), 0);
        }

        function test_returns_zero_for_missing_value_percent() {
            var volume = {
                "front-left": {}
            };
            compare(AudioDeviceData.extractVolumePercent(volume), 0);
        }

        function test_handles_hundred_percent_volume() {
            var volume = {
                "front-left": {
                    value_percent: "100%"
                }
            };
            compare(AudioDeviceData.extractVolumePercent(volume), 100);
        }

        function test_handles_zero_percent_volume() {
            var volume = {
                "front-left": {
                    value_percent: "0%"
                }
            };
            compare(AudioDeviceData.extractVolumePercent(volume), 0);
        }

        function test_handles_over_hundred_percent_volume() {
            var volume = {
                "front-left": {
                    value_percent: "153%"
                }
            };
            compare(AudioDeviceData.extractVolumePercent(volume), 153);
        }

        function test_handles_non_numeric_percent_string() {
            var volume = {
                "front-left": {
                    value_percent: "abc%"
                }
            };
            compare(AudioDeviceData.extractVolumePercent(volume), 0);
        }
    }
}
