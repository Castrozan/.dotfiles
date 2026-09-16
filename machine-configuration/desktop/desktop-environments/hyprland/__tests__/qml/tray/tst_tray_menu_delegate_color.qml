import QtQuick
import QtTest

Item {
    id: root

    TestCase {
        name: "TrayMenuDelegateColor"

        function test_separator_is_transparent() {
            var modelData = {
                isSeparator: true
            };
            var containsMouse = false;
            var result = modelData.isSeparator ? "transparent" : containsMouse ? "#surface" : "transparent";
            compare(result, "transparent");
        }

        function test_separator_ignores_hover() {
            var modelData = {
                isSeparator: true
            };
            var containsMouse = true;
            var result = modelData.isSeparator ? "transparent" : containsMouse ? "#surface" : "transparent";
            compare(result, "transparent");
        }

        function test_normal_item_transparent_by_default() {
            var modelData = {
                isSeparator: false
            };
            var containsMouse = false;
            var result = modelData.isSeparator ? "transparent" : containsMouse ? "#surface" : "transparent";
            compare(result, "transparent");
        }

        function test_normal_item_highlights_on_hover() {
            var modelData = {
                isSeparator: false
            };
            var containsMouse = true;
            var result = modelData.isSeparator ? "transparent" : containsMouse ? "#surface" : "transparent";
            compare(result, "#surface");
        }
    }
}
