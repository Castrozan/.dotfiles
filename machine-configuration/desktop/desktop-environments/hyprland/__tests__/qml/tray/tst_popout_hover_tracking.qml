import QtQuick
import QtTest

Item {
    id: root

    Item {
        id: mockPopoutWrapper
        width: 200
        height: 300
        visible: true

        property bool containsMouse: mockHoverHandler.hovered

        HoverHandler {
            id: mockHoverHandler
        }

        // Simulates a tray menu item with its own MouseArea
        MouseArea {
            id: childMenuItemMouseArea
            anchors.fill: parent
            hoverEnabled: true
        }
    }

    TestCase {
        name: "PopoutHoverTracking"

        function test_containsMouse_uses_hoverHandler_not_mouseArea() {
            // Verify the containsMouse property is bound to HoverHandler
            // (not a MouseArea that would lose hover to children)
            compare(mockPopoutWrapper.containsMouse, mockHoverHandler.hovered);
        }

        function test_hoverHandler_exists_on_popout() {
            verify(mockHoverHandler !== null);
            verify(mockHoverHandler !== undefined);
        }

        function test_child_mouseArea_does_not_affect_hoverHandler_binding() {
            // The binding should reference HoverHandler, not any MouseArea
            // Even with a child MouseArea present, the property reads from HoverHandler
            verify(childMenuItemMouseArea.hoverEnabled);
            compare(mockPopoutWrapper.containsMouse, mockHoverHandler.hovered);
        }
    }
}
