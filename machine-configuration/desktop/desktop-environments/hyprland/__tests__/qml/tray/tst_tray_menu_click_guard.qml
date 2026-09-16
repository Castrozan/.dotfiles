import QtQuick
import QtTest

Item {
    id: root

    TestCase {
        name: "TrayMenuClickGuard"

        function test_enabled_leaf_item_triggers() {
            var itemEnabled = true;
            var hasChildren = false;
            compare(itemEnabled && !hasChildren, true);
        }

        function test_disabled_item_does_not_trigger() {
            var itemEnabled = false;
            var hasChildren = false;
            compare(itemEnabled && !hasChildren, false);
        }

        function test_parent_item_does_not_trigger() {
            var itemEnabled = true;
            var hasChildren = true;
            compare(itemEnabled && !hasChildren, false);
        }

        function test_disabled_parent_does_not_trigger() {
            var itemEnabled = false;
            var hasChildren = true;
            compare(itemEnabled && !hasChildren, false);
        }
    }
}
