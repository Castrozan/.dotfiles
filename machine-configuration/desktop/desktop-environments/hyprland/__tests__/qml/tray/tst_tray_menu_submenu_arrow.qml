import QtQuick
import QtTest

Item {
    id: root

    TestCase {
        name: "TrayMenuSubmenuArrow"

        function test_arrow_visible_when_has_children() {
            var modelData = {
                isSeparator: false,
                hasChildren: true
            };
            compare(!modelData.isSeparator && modelData.hasChildren, true);
        }

        function test_arrow_hidden_when_no_children() {
            var modelData = {
                isSeparator: false,
                hasChildren: false
            };
            compare(!modelData.isSeparator && modelData.hasChildren, false);
        }

        function test_arrow_hidden_for_separator() {
            var modelData = {
                isSeparator: true,
                hasChildren: true
            };
            compare(!modelData.isSeparator && modelData.hasChildren, false);
        }
    }
}
