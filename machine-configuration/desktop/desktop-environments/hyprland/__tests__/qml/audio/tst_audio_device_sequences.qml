import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/dashboard/services/audio/AudioDeviceData.js" as AudioDeviceData

Item {
    TestCase {
        name: "AudioServiceDeviceListsAreEqual"

        function test_multiple_equal_items() {
            var listA = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                },
                {
                    name: "sink2",
                    volume: 80,
                    mute: true,
                    state: "IDLE",
                    description: "BT"
                }
            ];
            var listB = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                },
                {
                    name: "sink2",
                    volume: 80,
                    mute: true,
                    state: "IDLE",
                    description: "BT"
                }
            ];
            verify(AudioDeviceData.audioDeviceListsAreEqual(listA, listB));
        }

        function test_second_item_differs() {
            var listA = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                },
                {
                    name: "sink2",
                    volume: 80,
                    mute: true,
                    state: "IDLE",
                    description: "BT"
                }
            ];
            var listB = [
                {
                    name: "sink1",
                    volume: 50,
                    mute: false,
                    state: "RUNNING",
                    description: "Speaker"
                },
                {
                    name: "sink2",
                    volume: 99,
                    mute: true,
                    state: "IDLE",
                    description: "BT"
                }
            ];
            verify(!AudioDeviceData.audioDeviceListsAreEqual(listA, listB));
        }
    }
}
