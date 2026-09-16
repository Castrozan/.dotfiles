import QtQuick
import QtTest

Item {
    AudioDeviceSelectionFixture {
        id: audioServiceLogic
    }
    TestCase {
        name: "AudioServiceDefaultSinkDeviceType"

        function test_returns_speaker_when_no_default_sink() {
            audioServiceLogic.sinks = [];
            audioServiceLogic.defaultSinkName = "nonexistent";
            compare(audioServiceLogic.defaultSinkDeviceType, "speaker");
        }

        function test_returns_bluetooth_for_bluez_sink() {
            audioServiceLogic.sinks = [
                {
                    name: "bluez_output.AA_BB_CC_DD_EE_FF.1",
                    portType: ""
                }
            ];
            audioServiceLogic.defaultSinkName = "bluez_output.AA_BB_CC_DD_EE_FF.1";
            compare(audioServiceLogic.defaultSinkDeviceType, "bluetooth");
        }

        function test_returns_headphones_for_headset_port() {
            audioServiceLogic.sinks = [
                {
                    name: "alsa_output.pci-0000_00_1f.3.analog-stereo",
                    portType: "Headset"
                }
            ];
            audioServiceLogic.defaultSinkName = "alsa_output.pci-0000_00_1f.3.analog-stereo";
            compare(audioServiceLogic.defaultSinkDeviceType, "headphones");
        }

        function test_returns_headphones_for_headphones_port() {
            audioServiceLogic.sinks = [
                {
                    name: "alsa_output.pci-0000_00_1f.3.analog-stereo",
                    portType: "Headphones"
                }
            ];
            audioServiceLogic.defaultSinkName = "alsa_output.pci-0000_00_1f.3.analog-stereo";
            compare(audioServiceLogic.defaultSinkDeviceType, "headphones");
        }

        function test_returns_speaker_for_speaker_port() {
            audioServiceLogic.sinks = [
                {
                    name: "alsa_output.pci-0000_00_1f.3.analog-stereo",
                    portType: "Speaker"
                }
            ];
            audioServiceLogic.defaultSinkName = "alsa_output.pci-0000_00_1f.3.analog-stereo";
            compare(audioServiceLogic.defaultSinkDeviceType, "speaker");
        }

        function test_returns_speaker_for_empty_port_type() {
            audioServiceLogic.sinks = [
                {
                    name: "alsa_output.pci-0000_00_1f.3.analog-stereo",
                    portType: ""
                }
            ];
            audioServiceLogic.defaultSinkName = "alsa_output.pci-0000_00_1f.3.analog-stereo";
            compare(audioServiceLogic.defaultSinkDeviceType, "speaker");
        }
    }

    TestCase {
        name: "AudioServiceDefaultSinkIsBluetooth"

        function test_true_for_bluez_prefix() {
            audioServiceLogic.defaultSinkName = "bluez_output.AA_BB_CC_DD_EE_FF.1";
            verify(audioServiceLogic.defaultSinkIsBluetooth);
        }

        function test_false_for_alsa_prefix() {
            audioServiceLogic.defaultSinkName = "alsa_output.pci-0000_00_1f.3.analog-stereo";
            verify(!audioServiceLogic.defaultSinkIsBluetooth);
        }

        function test_false_for_empty_name() {
            audioServiceLogic.defaultSinkName = "";
            verify(!audioServiceLogic.defaultSinkIsBluetooth);
        }

        function test_false_for_name_containing_bluez_not_at_start() {
            audioServiceLogic.defaultSinkName = "alsa_bluez_something";
            verify(!audioServiceLogic.defaultSinkIsBluetooth);
        }
    }
}
