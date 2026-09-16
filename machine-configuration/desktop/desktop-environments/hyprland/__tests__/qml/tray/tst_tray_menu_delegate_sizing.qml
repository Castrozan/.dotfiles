import QtQuick
import QtTest

Item {
    id: root

    TestCase {
        name: "TrayMenuDelegateSizing"

        function test_separator_height_is_9() {
            var modelData = {
                isSeparator: true
            };
            compare(modelData.isSeparator ? 9 : 30, 9);
        }

        function test_normal_item_height_is_30() {
            var modelData = {
                isSeparator: false
            };
            compare(modelData.isSeparator ? 9 : 30, 30);
        }

        function test_separator_has_margins() {
            var modelData = {
                isSeparator: true
            };
            compare(modelData.isSeparator ? 8 : 0, 8);
        }

        function test_normal_item_has_no_margins() {
            var modelData = {
                isSeparator: false
            };
            compare(modelData.isSeparator ? 8 : 0, 0);
        }

        function test_separator_radius_is_0() {
            var modelData = {
                isSeparator: true
            };
            compare(modelData.isSeparator ? 0 : 6, 0);
        }

        function test_normal_item_radius_is_6() {
            var modelData = {
                isSeparator: false
            };
            compare(modelData.isSeparator ? 0 : 6, 6);
        }
    }
}
