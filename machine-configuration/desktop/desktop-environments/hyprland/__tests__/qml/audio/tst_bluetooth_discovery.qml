import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/dashboard/services/audio"

Item {
    BluetoothDeviceDiscovery {
        id: bluetoothDiscovery
        previousPairedDevices: []
        onPairedDevicesDiscovered: devices => previousPairedDevices = devices
    }

    TestCase {
        name: "AudioServiceMergePairedDevices"

        function test_merges_paired_with_connected_status() {
            bluetoothDiscovery._pairedDevicesList = [
                {
                    mac: "AA:BB:CC:DD:EE:01",
                    name: "Speaker"
                },
                {
                    mac: "AA:BB:CC:DD:EE:02",
                    name: "Headphones"
                }
            ];
            bluetoothDiscovery._connectedMacs = {
                "AA:BB:CC:DD:EE:02": true
            };
            bluetoothDiscovery.previousPairedDevices = [];
            bluetoothDiscovery._mergePairedDevices();

            compare(bluetoothDiscovery.previousPairedDevices.length, 2);
            compare(bluetoothDiscovery.previousPairedDevices[0].mac, "AA:BB:CC:DD:EE:02");
            verify(bluetoothDiscovery.previousPairedDevices[0].connected);
            compare(bluetoothDiscovery.previousPairedDevices[1].mac, "AA:BB:CC:DD:EE:01");
            verify(!bluetoothDiscovery.previousPairedDevices[1].connected);
        }

        function test_all_disconnected() {
            bluetoothDiscovery._pairedDevicesList = [
                {
                    mac: "AA:BB:CC:DD:EE:01",
                    name: "Device A"
                },
                {
                    mac: "AA:BB:CC:DD:EE:02",
                    name: "Device B"
                }
            ];
            bluetoothDiscovery._connectedMacs = {};
            bluetoothDiscovery.previousPairedDevices = [];
            bluetoothDiscovery._mergePairedDevices();

            compare(bluetoothDiscovery.previousPairedDevices.length, 2);
            verify(!bluetoothDiscovery.previousPairedDevices[0].connected);
            verify(!bluetoothDiscovery.previousPairedDevices[1].connected);
        }

        function test_empty_paired_list_does_not_overwrite_existing() {
            bluetoothDiscovery.previousPairedDevices = [
                {
                    mac: "existing",
                    name: "Existing",
                    connected: false
                }
            ];
            bluetoothDiscovery._pairedDevicesList = [];
            bluetoothDiscovery._connectedMacs = {};
            bluetoothDiscovery._mergePairedDevices();

            compare(bluetoothDiscovery.previousPairedDevices.length, 1);
            compare(bluetoothDiscovery.previousPairedDevices[0].mac, "existing");
        }

        function test_empty_paired_list_overwrites_empty_existing() {
            bluetoothDiscovery.previousPairedDevices = [];
            bluetoothDiscovery._pairedDevicesList = [];
            bluetoothDiscovery._connectedMacs = {};
            bluetoothDiscovery._mergePairedDevices();

            compare(bluetoothDiscovery.previousPairedDevices.length, 0);
        }

        function test_connected_devices_sort_first() {
            bluetoothDiscovery._pairedDevicesList = [
                {
                    mac: "01",
                    name: "First"
                },
                {
                    mac: "02",
                    name: "Second"
                },
                {
                    mac: "03",
                    name: "Third"
                }
            ];
            bluetoothDiscovery._connectedMacs = {
                "03": true
            };
            bluetoothDiscovery.previousPairedDevices = [];
            bluetoothDiscovery._mergePairedDevices();

            compare(bluetoothDiscovery.previousPairedDevices[0].mac, "03");
            verify(bluetoothDiscovery.previousPairedDevices[0].connected);
        }

        function test_preserves_device_names() {
            bluetoothDiscovery._pairedDevicesList = [
                {
                    mac: "AA:BB:CC:DD:EE:01",
                    name: "Sony WH-1000XM5"
                }
            ];
            bluetoothDiscovery._connectedMacs = {
                "AA:BB:CC:DD:EE:01": true
            };
            bluetoothDiscovery.previousPairedDevices = [];
            bluetoothDiscovery._mergePairedDevices();

            compare(bluetoothDiscovery.previousPairedDevices[0].name, "Sony WH-1000XM5");
        }
    }
}
