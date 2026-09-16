import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/dashboard/services/audio/AudioDeviceData.js" as AudioDeviceData

Item {
    TestCase {
        name: "AudioServiceDeviceListsAreEqual"

        function test_equal_empty_lists() {
            verify(AudioDeviceData.audioDeviceListsAreEqual([], []));
        }

        function test_equal_single_element_lists() {
            var listA = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                }
            ];
            var listB = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                }
            ];
            verify(AudioDeviceData.audioDeviceListsAreEqual(listA, listB));
        }

        function test_different_lengths() {
            var listA = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                }
            ];
            verify(!AudioDeviceData.audioDeviceListsAreEqual(listA, []));
        }

        function test_different_names() {
            var listA = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                }
            ];
            var listB = [
                {
                    name: "sink2",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                }
            ];
            verify(!AudioDeviceData.audioDeviceListsAreEqual(listA, listB));
        }

        function test_different_volumes() {
            var listA = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                }
            ];
            var listB = [
                {
                    name: "sink1",
                    volume: 75,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                }
            ];
            verify(!AudioDeviceData.audioDeviceListsAreEqual(listA, listB));
        }

        function test_different_mute() {
            var listA = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                }
            ];
            var listB = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: true,
                    state: "RUNNING",
                    description: "Speaker"
                }
            ];
            verify(!AudioDeviceData.audioDeviceListsAreEqual(listA, listB));
        }

        function test_different_state() {
            var listA = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                }
            ];
            var listB = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "IDLE",
                    description: "Speaker"
                }
            ];
            verify(!AudioDeviceData.audioDeviceListsAreEqual(listA, listB));
        }

        function test_different_description() {
            var listA = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                }
            ];
            var listB = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Headphones"
                }
            ];
            verify(!AudioDeviceData.audioDeviceListsAreEqual(listA, listB));
        }
    }
}
