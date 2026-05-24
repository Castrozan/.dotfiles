import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: audioServiceLogic

        property var sinks: []
        property string defaultSinkName: ""
        property var cards: []
        property var pairedDevices: []
        property var _pairedDevicesList: []
        property var _connectedMacs: ({})

        readonly property var defaultSink: {
            for (let i = 0; i < sinks.length; i++)
                if (sinks[i].name === defaultSinkName)
                    return sinks[i];
            return null;
        }

        readonly property bool defaultSinkIsBluetooth: defaultSinkName.startsWith("bluez_")

        readonly property string defaultSinkDeviceType: {
            if (!defaultSink)
                return "speaker";
            if (defaultSinkName.startsWith("bluez_"))
                return "bluetooth";
            const portType = (defaultSink.portType ?? "").toLowerCase();
            if (portType === "headset" || portType === "headphones")
                return "headphones";
            return "speaker";
        }

        function _extractVolumePercent(volumeObject) {
            if (!volumeObject)
                return 0;
            for (const channel in volumeObject) {
                const percentString = volumeObject[channel].value_percent ?? "0%";
                return parseInt(percentString) || 0;
            }
            return 0;
        }

        function _extractPortType(ports, activePortName) {
            if (!ports || !activePortName)
                return "";
            for (let i = 0; i < ports.length; i++)
                if (ports[i].name === activePortName)
                    return ports[i].type ?? "";
            return "";
        }

        function _audioDeviceListsAreEqual(oldList, newList) {
            if (oldList.length !== newList.length)
                return false;
            for (let i = 0; i < oldList.length; i++) {
                const oldItem = oldList[i];
                const newItem = newList[i];
                if (oldItem.name !== newItem.name || oldItem.volume !== newItem.volume || oldItem.mute !== newItem.mute || oldItem.state !== newItem.state || oldItem.description !== newItem.description)
                    return false;
            }
            return true;
        }

        function cardForBluetoothMac(macAddress) {
            const normalizedMac = macAddress.replace(/:/g, "_");
            for (let i = 0; i < cards.length; i++)
                if (cards[i].name.indexOf(normalizedMac) !== -1)
                    return cards[i];
            return null;
        }

        function _mergePairedDevices() {
            const merged = _pairedDevicesList.map(function(device) {
                return {
                    mac: device.mac,
                    name: device.name,
                    connected: _connectedMacs[device.mac] === true
                };
            });
            merged.sort(function(a, b) {
                return (b.connected ? 1 : 0) - (a.connected ? 1 : 0);
            });
            if (merged.length > 0 || pairedDevices.length === 0)
                pairedDevices = merged;
        }
    }

    TestCase {
        name: "AudioServiceExtractVolumePercent"

        function test_extracts_volume_from_single_channel() {
            var volume = { "front-left": { value_percent: "75%" } };
            compare(audioServiceLogic._extractVolumePercent(volume), 75);
        }

        function test_extracts_volume_from_multi_channel() {
            var volume = {
                "front-left": { value_percent: "50%" },
                "front-right": { value_percent: "60%" }
            };
            compare(audioServiceLogic._extractVolumePercent(volume), 50);
        }

        function test_returns_zero_for_null_volume() {
            compare(audioServiceLogic._extractVolumePercent(null), 0);
        }

        function test_returns_zero_for_undefined_volume() {
            compare(audioServiceLogic._extractVolumePercent(undefined), 0);
        }

        function test_returns_zero_for_empty_volume_object() {
            compare(audioServiceLogic._extractVolumePercent({}), 0);
        }

        function test_returns_zero_for_missing_value_percent() {
            var volume = { "front-left": {} };
            compare(audioServiceLogic._extractVolumePercent(volume), 0);
        }

        function test_handles_hundred_percent_volume() {
            var volume = { "front-left": { value_percent: "100%" } };
            compare(audioServiceLogic._extractVolumePercent(volume), 100);
        }

        function test_handles_zero_percent_volume() {
            var volume = { "front-left": { value_percent: "0%" } };
            compare(audioServiceLogic._extractVolumePercent(volume), 0);
        }

        function test_handles_over_hundred_percent_volume() {
            var volume = { "front-left": { value_percent: "153%" } };
            compare(audioServiceLogic._extractVolumePercent(volume), 153);
        }

        function test_handles_non_numeric_percent_string() {
            var volume = { "front-left": { value_percent: "abc%" } };
            compare(audioServiceLogic._extractVolumePercent(volume), 0);
        }
    }

    TestCase {
        name: "AudioServiceExtractPortType"

        function test_finds_matching_port_type() {
            var ports = [
                { name: "analog-output-speaker", type: "Speaker" },
                { name: "analog-output-headphones", type: "Headphones" }
            ];
            compare(audioServiceLogic._extractPortType(ports, "analog-output-headphones"), "Headphones");
        }

        function test_returns_empty_for_no_matching_port() {
            var ports = [
                { name: "analog-output-speaker", type: "Speaker" }
            ];
            compare(audioServiceLogic._extractPortType(ports, "nonexistent-port"), "");
        }

        function test_returns_empty_for_null_ports() {
            compare(audioServiceLogic._extractPortType(null, "some-port"), "");
        }

        function test_returns_empty_for_null_active_port() {
            var ports = [{ name: "port", type: "Speaker" }];
            compare(audioServiceLogic._extractPortType(ports, null), "");
        }

        function test_returns_empty_for_undefined_active_port() {
            var ports = [{ name: "port", type: "Speaker" }];
            compare(audioServiceLogic._extractPortType(ports, undefined), "");
        }

        function test_returns_empty_for_empty_ports_array() {
            compare(audioServiceLogic._extractPortType([], "some-port"), "");
        }

        function test_returns_empty_string_when_port_has_no_type() {
            var ports = [{ name: "some-port" }];
            compare(audioServiceLogic._extractPortType(ports, "some-port"), "");
        }

        function test_finds_first_matching_port() {
            var ports = [
                { name: "dup-port", type: "FirstType" },
                { name: "dup-port", type: "SecondType" }
            ];
            compare(audioServiceLogic._extractPortType(ports, "dup-port"), "FirstType");
        }
    }

    TestCase {
        name: "AudioServiceDeviceListsAreEqual"

        function test_equal_empty_lists() {
            verify(audioServiceLogic._audioDeviceListsAreEqual([], []));
        }

        function test_equal_single_element_lists() {
            var listA = [{ name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Speaker" }];
            var listB = [{ name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Speaker" }];
            verify(audioServiceLogic._audioDeviceListsAreEqual(listA, listB));
        }

        function test_different_lengths() {
            var listA = [{ name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Speaker" }];
            verify(!audioServiceLogic._audioDeviceListsAreEqual(listA, []));
        }

        function test_different_names() {
            var listA = [{ name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Speaker" }];
            var listB = [{ name: "sink2", volume: 50, mute: false, state: "RUNNING", description: "Speaker" }];
            verify(!audioServiceLogic._audioDeviceListsAreEqual(listA, listB));
        }

        function test_different_volumes() {
            var listA = [{ name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Speaker" }];
            var listB = [{ name: "sink1", volume: 75, mute: false, state: "RUNNING", description: "Speaker" }];
            verify(!audioServiceLogic._audioDeviceListsAreEqual(listA, listB));
        }

        function test_different_mute() {
            var listA = [{ name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Speaker" }];
            var listB = [{ name: "sink1", volume: 50, mute: true, state: "RUNNING", description: "Speaker" }];
            verify(!audioServiceLogic._audioDeviceListsAreEqual(listA, listB));
        }

        function test_different_state() {
            var listA = [{ name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Speaker" }];
            var listB = [{ name: "sink1", volume: 50, mute: false, state: "IDLE", description: "Speaker" }];
            verify(!audioServiceLogic._audioDeviceListsAreEqual(listA, listB));
        }

        function test_different_description() {
            var listA = [{ name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Speaker" }];
            var listB = [{ name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Headphones" }];
            verify(!audioServiceLogic._audioDeviceListsAreEqual(listA, listB));
        }

        function test_multiple_equal_items() {
            var listA = [
                { name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Speaker" },
                { name: "sink2", volume: 80, mute: true, state: "IDLE", description: "BT" }
            ];
            var listB = [
                { name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Speaker" },
                { name: "sink2", volume: 80, mute: true, state: "IDLE", description: "BT" }
            ];
            verify(audioServiceLogic._audioDeviceListsAreEqual(listA, listB));
        }

        function test_second_item_differs() {
            var listA = [
                { name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Speaker" },
                { name: "sink2", volume: 80, mute: true, state: "IDLE", description: "BT" }
            ];
            var listB = [
                { name: "sink1", volume: 50, mute: false, state: "RUNNING", description: "Speaker" },
                { name: "sink2", volume: 99, mute: true, state: "IDLE", description: "BT" }
            ];
            verify(!audioServiceLogic._audioDeviceListsAreEqual(listA, listB));
        }
    }

    TestCase {
        name: "AudioServiceCardForBluetoothMac"

        function test_finds_card_by_mac_with_colons() {
            audioServiceLogic.cards = [
                { name: "bluez_card.AA_BB_CC_DD_EE_FF", activeProfile: "a2dp-sink" },
                { name: "alsa_card.pci-0000_00_1f.3", activeProfile: "output:analog-stereo" }
            ];
            var result = audioServiceLogic.cardForBluetoothMac("AA:BB:CC:DD:EE:FF");
            verify(result !== null);
            compare(result.name, "bluez_card.AA_BB_CC_DD_EE_FF");
        }

        function test_returns_null_when_no_matching_card() {
            audioServiceLogic.cards = [
                { name: "alsa_card.pci-0000_00_1f.3", activeProfile: "output:analog-stereo" }
            ];
            compare(audioServiceLogic.cardForBluetoothMac("AA:BB:CC:DD:EE:FF"), null);
        }

        function test_returns_null_for_empty_cards() {
            audioServiceLogic.cards = [];
            compare(audioServiceLogic.cardForBluetoothMac("AA:BB:CC:DD:EE:FF"), null);
        }

        function test_normalizes_colons_to_underscores() {
            audioServiceLogic.cards = [
                { name: "bluez_card.11_22_33_44_55_66", activeProfile: "a2dp-sink" }
            ];
            var result = audioServiceLogic.cardForBluetoothMac("11:22:33:44:55:66");
            verify(result !== null);
            compare(result.name, "bluez_card.11_22_33_44_55_66");
        }

        function test_mac_already_has_underscores() {
            audioServiceLogic.cards = [
                { name: "bluez_card.11_22_33_44_55_66", activeProfile: "a2dp-sink" }
            ];
            var result = audioServiceLogic.cardForBluetoothMac("11_22_33_44_55_66");
            verify(result !== null);
        }
    }

    TestCase {
        name: "AudioServiceDefaultSinkDeviceType"

        function test_returns_speaker_when_no_default_sink() {
            audioServiceLogic.sinks = [];
            audioServiceLogic.defaultSinkName = "nonexistent";
            compare(audioServiceLogic.defaultSinkDeviceType, "speaker");
        }

        function test_returns_bluetooth_for_bluez_sink() {
            audioServiceLogic.sinks = [{ name: "bluez_output.AA_BB_CC_DD_EE_FF.1", portType: "" }];
            audioServiceLogic.defaultSinkName = "bluez_output.AA_BB_CC_DD_EE_FF.1";
            compare(audioServiceLogic.defaultSinkDeviceType, "bluetooth");
        }

        function test_returns_headphones_for_headset_port() {
            audioServiceLogic.sinks = [{ name: "alsa_output.pci-0000_00_1f.3.analog-stereo", portType: "Headset" }];
            audioServiceLogic.defaultSinkName = "alsa_output.pci-0000_00_1f.3.analog-stereo";
            compare(audioServiceLogic.defaultSinkDeviceType, "headphones");
        }

        function test_returns_headphones_for_headphones_port() {
            audioServiceLogic.sinks = [{ name: "alsa_output.pci-0000_00_1f.3.analog-stereo", portType: "Headphones" }];
            audioServiceLogic.defaultSinkName = "alsa_output.pci-0000_00_1f.3.analog-stereo";
            compare(audioServiceLogic.defaultSinkDeviceType, "headphones");
        }

        function test_returns_speaker_for_speaker_port() {
            audioServiceLogic.sinks = [{ name: "alsa_output.pci-0000_00_1f.3.analog-stereo", portType: "Speaker" }];
            audioServiceLogic.defaultSinkName = "alsa_output.pci-0000_00_1f.3.analog-stereo";
            compare(audioServiceLogic.defaultSinkDeviceType, "speaker");
        }

        function test_returns_speaker_for_empty_port_type() {
            audioServiceLogic.sinks = [{ name: "alsa_output.pci-0000_00_1f.3.analog-stereo", portType: "" }];
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

    TestCase {
        name: "AudioServiceMergePairedDevices"

        function test_merges_paired_with_connected_status() {
            audioServiceLogic._pairedDevicesList = [
                { mac: "AA:BB:CC:DD:EE:01", name: "Speaker" },
                { mac: "AA:BB:CC:DD:EE:02", name: "Headphones" }
            ];
            audioServiceLogic._connectedMacs = { "AA:BB:CC:DD:EE:02": true };
            audioServiceLogic.pairedDevices = [];
            audioServiceLogic._mergePairedDevices();

            compare(audioServiceLogic.pairedDevices.length, 2);
            compare(audioServiceLogic.pairedDevices[0].mac, "AA:BB:CC:DD:EE:02");
            verify(audioServiceLogic.pairedDevices[0].connected);
            compare(audioServiceLogic.pairedDevices[1].mac, "AA:BB:CC:DD:EE:01");
            verify(!audioServiceLogic.pairedDevices[1].connected);
        }

        function test_all_disconnected() {
            audioServiceLogic._pairedDevicesList = [
                { mac: "AA:BB:CC:DD:EE:01", name: "Device A" },
                { mac: "AA:BB:CC:DD:EE:02", name: "Device B" }
            ];
            audioServiceLogic._connectedMacs = {};
            audioServiceLogic.pairedDevices = [];
            audioServiceLogic._mergePairedDevices();

            compare(audioServiceLogic.pairedDevices.length, 2);
            verify(!audioServiceLogic.pairedDevices[0].connected);
            verify(!audioServiceLogic.pairedDevices[1].connected);
        }

        function test_empty_paired_list_does_not_overwrite_existing() {
            audioServiceLogic.pairedDevices = [{ mac: "existing", name: "Existing", connected: false }];
            audioServiceLogic._pairedDevicesList = [];
            audioServiceLogic._connectedMacs = {};
            audioServiceLogic._mergePairedDevices();

            compare(audioServiceLogic.pairedDevices.length, 1);
            compare(audioServiceLogic.pairedDevices[0].mac, "existing");
        }

        function test_empty_paired_list_overwrites_empty_existing() {
            audioServiceLogic.pairedDevices = [];
            audioServiceLogic._pairedDevicesList = [];
            audioServiceLogic._connectedMacs = {};
            audioServiceLogic._mergePairedDevices();

            compare(audioServiceLogic.pairedDevices.length, 0);
        }

        function test_connected_devices_sort_first() {
            audioServiceLogic._pairedDevicesList = [
                { mac: "01", name: "First" },
                { mac: "02", name: "Second" },
                { mac: "03", name: "Third" }
            ];
            audioServiceLogic._connectedMacs = { "03": true };
            audioServiceLogic.pairedDevices = [];
            audioServiceLogic._mergePairedDevices();

            compare(audioServiceLogic.pairedDevices[0].mac, "03");
            verify(audioServiceLogic.pairedDevices[0].connected);
        }

        function test_preserves_device_names() {
            audioServiceLogic._pairedDevicesList = [
                { mac: "AA:BB:CC:DD:EE:01", name: "Sony WH-1000XM5" }
            ];
            audioServiceLogic._connectedMacs = { "AA:BB:CC:DD:EE:01": true };
            audioServiceLogic.pairedDevices = [];
            audioServiceLogic._mergePairedDevices();

            compare(audioServiceLogic.pairedDevices[0].name, "Sony WH-1000XM5");
        }
    }
}
