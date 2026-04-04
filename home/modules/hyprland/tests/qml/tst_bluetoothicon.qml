import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: bluetoothIcon

        property bool isPowered: true
        property bool hasConnectedDevices: false

        function iconText() {
            if (!isPowered) return "󰂲";
            if (hasConnectedDevices) return "󰂱";
            return "󰂯";
        }
    }

    TestCase {
        name: "BluetoothIconDefaults"

        function init() {
            bluetoothIcon.isPowered = true;
            bluetoothIcon.hasConnectedDevices = false;
        }

        function test_default_state_shows_idle_icon() {
            compare(bluetoothIcon.iconText(), "󰂯");
        }

        function test_default_state_never_returns_empty() {
            verify(bluetoothIcon.iconText() !== "");
        }
    }

    TestCase {
        name: "BluetoothIconStates"

        function init() {
            bluetoothIcon.isPowered = true;
            bluetoothIcon.hasConnectedDevices = false;
        }

        function test_powered_off_shows_off_icon() {
            bluetoothIcon.isPowered = false;
            compare(bluetoothIcon.iconText(), "󰂲");
        }

        function test_powered_off_with_connected_still_shows_off() {
            bluetoothIcon.isPowered = false;
            bluetoothIcon.hasConnectedDevices = true;
            compare(bluetoothIcon.iconText(), "󰂲");
        }

        function test_connected_shows_connected_icon() {
            bluetoothIcon.hasConnectedDevices = true;
            compare(bluetoothIcon.iconText(), "󰂱");
        }

        function test_powered_no_connections_shows_idle_icon() {
            compare(bluetoothIcon.iconText(), "󰂯");
        }

        function test_all_states_return_nonempty_icon() {
            var states = [
                { powered: false, connected: false },
                { powered: false, connected: true },
                { powered: true,  connected: false },
                { powered: true,  connected: true }
            ];
            for (var i = 0; i < states.length; i++) {
                bluetoothIcon.isPowered = states[i].powered;
                bluetoothIcon.hasConnectedDevices = states[i].connected;
                verify(bluetoothIcon.iconText() !== "",
                    "icon empty for powered=" + states[i].powered + " connected=" + states[i].connected);
            }
        }

        function test_three_distinct_icons() {
            bluetoothIcon.isPowered = false;
            var offIcon = bluetoothIcon.iconText();

            bluetoothIcon.isPowered = true;
            bluetoothIcon.hasConnectedDevices = false;
            var idleIcon = bluetoothIcon.iconText();

            bluetoothIcon.hasConnectedDevices = true;
            var connectedIcon = bluetoothIcon.iconText();

            verify(offIcon !== idleIcon);
            verify(offIcon !== connectedIcon);
            verify(idleIcon !== connectedIcon);
        }
    }
}
