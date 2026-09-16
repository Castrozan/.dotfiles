import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/dashboard/services/audio/AudioDeviceData.js" as AudioDeviceData

Item {
    TestCase {
        name: "AudioServiceExtractPortType"

        function test_finds_matching_port_type() {
            var ports = [
                {
                    name: "analog-output-speaker",
                    type: "Speaker"
                },
                {
                    name: "analog-output-headphones",
                    type: "Headphones"
                }
            ];
            compare(AudioDeviceData.extractPortType(ports, "analog-output-headphones"), "Headphones");
        }

        function test_returns_empty_for_no_matching_port() {
            var ports = [
                {
                    name: "analog-output-speaker",
                    type: "Speaker"
                }
            ];
            compare(AudioDeviceData.extractPortType(ports, "nonexistent-port"), "");
        }

        function test_returns_empty_for_null_ports() {
            compare(AudioDeviceData.extractPortType(null, "some-port"), "");
        }

        function test_returns_empty_for_null_active_port() {
            var ports = [
                {
                    name: "port",
                    type: "Speaker"
                }
            ];
            compare(AudioDeviceData.extractPortType(ports, null), "");
        }

        function test_returns_empty_for_undefined_active_port() {
            var ports = [
                {
                    name: "port",
                    type: "Speaker"
                }
            ];
            compare(AudioDeviceData.extractPortType(ports, undefined), "");
        }

        function test_returns_empty_for_empty_ports_array() {
            compare(AudioDeviceData.extractPortType([], "some-port"), "");
        }

        function test_returns_empty_string_when_port_has_no_type() {
            var ports = [
                {
                    name: "some-port"
                }
            ];
            compare(AudioDeviceData.extractPortType(ports, "some-port"), "");
        }

        function test_finds_first_matching_port() {
            var ports = [
                {
                    name: "dup-port",
                    type: "FirstType"
                },
                {
                    name: "dup-port",
                    type: "SecondType"
                }
            ];
            compare(AudioDeviceData.extractPortType(ports, "dup-port"), "FirstType");
        }
    }
}
