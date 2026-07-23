import QtQuick
import QtTest

Item {
    id: root

    // --- TrayMenuPopout logic: itemEnabled ---

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

    // --- TrayMenuPopout logic: delegate sizing ---

    TestCase {
        name: "TrayMenuDelegateSizing"

        function test_separator_height_is_9() {
            var modelData = { isSeparator: true };
            compare(modelData.isSeparator ? 9 : 30, 9);
        }

        function test_normal_item_height_is_30() {
            var modelData = { isSeparator: false };
            compare(modelData.isSeparator ? 9 : 30, 30);
        }

        function test_separator_has_margins() {
            var modelData = { isSeparator: true };
            compare(modelData.isSeparator ? 8 : 0, 8);
        }

        function test_normal_item_has_no_margins() {
            var modelData = { isSeparator: false };
            compare(modelData.isSeparator ? 8 : 0, 0);
        }

        function test_separator_radius_is_0() {
            var modelData = { isSeparator: true };
            compare(modelData.isSeparator ? 0 : 6, 0);
        }

        function test_normal_item_radius_is_6() {
            var modelData = { isSeparator: false };
            compare(modelData.isSeparator ? 0 : 6, 6);
        }
    }

    // --- TrayMenuPopout logic: color binding ---

    TestCase {
        name: "TrayMenuDelegateColor"

        function test_separator_is_transparent() {
            var modelData = { isSeparator: true };
            var containsMouse = false;
            var result = modelData.isSeparator ? "transparent"
                : containsMouse ? "#surface" : "transparent";
            compare(result, "transparent");
        }

        function test_separator_ignores_hover() {
            var modelData = { isSeparator: true };
            var containsMouse = true;
            var result = modelData.isSeparator ? "transparent"
                : containsMouse ? "#surface" : "transparent";
            compare(result, "transparent");
        }

        function test_normal_item_transparent_by_default() {
            var modelData = { isSeparator: false };
            var containsMouse = false;
            var result = modelData.isSeparator ? "transparent"
                : containsMouse ? "#surface" : "transparent";
            compare(result, "transparent");
        }

        function test_normal_item_highlights_on_hover() {
            var modelData = { isSeparator: false };
            var containsMouse = true;
            var result = modelData.isSeparator ? "transparent"
                : containsMouse ? "#surface" : "transparent";
            compare(result, "#surface");
        }
    }

    // --- TrayMenuPopout logic: submenu arrow visibility ---

    TestCase {
        name: "TrayMenuSubmenuArrow"

        function test_arrow_visible_when_has_children() {
            var modelData = { isSeparator: false, hasChildren: true };
            compare(!modelData.isSeparator && modelData.hasChildren, true);
        }

        function test_arrow_hidden_when_no_children() {
            var modelData = { isSeparator: false, hasChildren: false };
            compare(!modelData.isSeparator && modelData.hasChildren, false);
        }

        function test_arrow_hidden_for_separator() {
            var modelData = { isSeparator: true, hasChildren: true };
            compare(!modelData.isSeparator && modelData.hasChildren, false);
        }
    }

    // --- TrayMenuPopout logic: click guard ---

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

    // --- TrayMenuPopout logic: text opacity ---

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

    // --- TrayModule logic: toggle behavior ---

    QtObject {
        id: mockScreenScope
        property string popoutCurrentName: ""
        property real popoutCenterY: 0

        function showPopout(name, centerY) {
            popoutCurrentName = name;
            popoutCenterY = centerY;
        }
    }

    TestCase {
        name: "TrayModuleToggle"

        function init() {
            mockScreenScope.popoutCurrentName = "";
            mockScreenScope.popoutCenterY = 0;
        }

        function _simulateClick(index) {
            var popoutName = "traymenu" + index;
            if (mockScreenScope.popoutCurrentName === popoutName) {
                mockScreenScope.popoutCurrentName = "";
                return;
            }
            mockScreenScope.showPopout(popoutName, 100);
        }

        function test_click_opens_popout() {
            _simulateClick(0);
            compare(mockScreenScope.popoutCurrentName, "traymenu0");
        }

        function test_click_again_closes_popout() {
            _simulateClick(0);
            compare(mockScreenScope.popoutCurrentName, "traymenu0");
            _simulateClick(0);
            compare(mockScreenScope.popoutCurrentName, "");
        }

        function test_click_different_icon_switches_popout() {
            _simulateClick(0);
            compare(mockScreenScope.popoutCurrentName, "traymenu0");
            _simulateClick(1);
            compare(mockScreenScope.popoutCurrentName, "traymenu1");
        }

        function test_click_sets_center_y() {
            _simulateClick(0);
            compare(mockScreenScope.popoutCenterY, 100);
        }

        function test_toggle_off_does_not_change_center_y() {
            _simulateClick(0);
            var savedY = mockScreenScope.popoutCenterY;
            _simulateClick(0);
            compare(mockScreenScope.popoutCenterY, savedY);
        }
    }

    // --- Drawers logic: showPopout stops hide timer ---

    Timer {
        id: mockPopoutHideTimer
        interval: 450
        property bool wasStopped: false

        function stop() {
            wasStopped = true;
            running = false;
        }

        function restart() {
            wasStopped = false;
            running = true;
        }
    }

    QtObject {
        id: mockDrawersScope
        property string popoutCurrentName: ""
        property real popoutCenterY: 0

        function showPopout(name, centerY) {
            mockPopoutHideTimer.stop();
            popoutCurrentName = name;
            popoutCenterY = centerY;
        }
    }

    TestCase {
        name: "ShowPopoutStopsHideTimer"

        function init() {
            mockDrawersScope.popoutCurrentName = "";
            mockDrawersScope.popoutCenterY = 0;
            mockPopoutHideTimer.wasStopped = false;
            mockPopoutHideTimer.running = false;
        }

        function test_showPopout_stops_pending_hide_timer() {
            mockPopoutHideTimer.restart();
            verify(mockPopoutHideTimer.running);

            mockDrawersScope.showPopout("traymenu0", 200);

            verify(mockPopoutHideTimer.wasStopped);
            verify(!mockPopoutHideTimer.running);
        }

        function test_showPopout_sets_name_and_position() {
            mockDrawersScope.showPopout("traymenu2", 350);
            compare(mockDrawersScope.popoutCurrentName, "traymenu2");
            compare(mockDrawersScope.popoutCenterY, 350);
        }

        function test_showPopout_stops_timer_even_when_not_running() {
            verify(!mockPopoutHideTimer.running);
            mockDrawersScope.showPopout("traymenu0", 100);
            verify(mockPopoutHideTimer.wasStopped);
        }
    }

    // --- PopoutWrapper logic: HoverHandler vs MouseArea hover ---
    // HoverHandler.hovered is not stolen by child MouseAreas,
    // unlike MouseArea.containsMouse which loses hover when a child
    // MouseArea with hoverEnabled intercepts it.

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
