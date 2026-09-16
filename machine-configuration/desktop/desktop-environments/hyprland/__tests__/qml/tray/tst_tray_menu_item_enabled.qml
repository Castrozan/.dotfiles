import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: enabledItem
        property var enabled: true
        readonly property bool itemEnabled: enabled !== false
    }

    QtObject {
        id: disabledItem
        property var enabled: false
        readonly property bool itemEnabled: enabled !== false
    }

    QtObject {
        id: undefinedEnabledItem
        property var enabled: undefined
        readonly property bool itemEnabled: enabled !== false
    }

    QtObject {
        id: nullEnabledItem
        property var enabled: null
        readonly property bool itemEnabled: enabled !== false
    }

    TestCase {
        name: "TrayMenuItemEnabled"

        function test_enabled_true_is_enabled() {
            compare(enabledItem.itemEnabled, true);
        }

        function test_enabled_false_is_disabled() {
            compare(disabledItem.itemEnabled, false);
        }

        function test_enabled_undefined_defaults_to_enabled() {
            compare(undefinedEnabledItem.itemEnabled, true);
        }

        function test_enabled_null_defaults_to_enabled() {
            compare(nullEnabledItem.itemEnabled, true);
        }
    }
}
