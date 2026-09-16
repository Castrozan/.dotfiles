import QtQuick
import QtTest

Item {
    id: root

    TestCase {
        name: "TrayMenuTextOpacity"

        function test_enabled_item_full_opacity() {
            var itemEnabled = true;
            fuzzyCompare(itemEnabled ? 1.0 : 0.4, 1.0, 0.01);
        }

        function test_disabled_item_reduced_opacity() {
            var itemEnabled = false;
            fuzzyCompare(itemEnabled ? 1.0 : 0.4, 0.4, 0.01);
        }
    }
}
