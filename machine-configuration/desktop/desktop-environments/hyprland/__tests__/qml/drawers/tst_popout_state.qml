import QtQuick
import QtTest

DrawerStateFixture {
    id: root

    TestCase {
        name: "DrawerStatePopout"

        function init() {
            drawerState.clearPopout();
            drawerState.setPopoutHovered(false);
            drawerState.popoutIconHovered = false;
            popoutShownSpy.clear();
            popoutHideRequestedSpy.clear();
        }

        function test_show_popout_by_name_uses_resolved_center_data() {
            return root.popoutNameCases;
        }

        function test_show_popout_by_name_uses_resolved_center(data) {
            drawerState.showPopoutByName(data.name);
            compare(drawerState.popoutCurrentName, data.name);
            compare(drawerState.popoutCenterY, root.popoutCenterYByName[data.name]);
            verify(drawerState.hasActivePopout);
        }

        function test_show_popout_reports_every_show() {
            drawerState.showPopout("network", 12);
            drawerState.showPopout("network", 34);
            compare(popoutShownSpy.count, 2);
            compare(drawerState.popoutCenterY, 34);
        }

        function test_toggle_popout_repeated_alternates() {
            drawerState.togglePopout("network");
            compare(drawerState.popoutCurrentName, "network");
            drawerState.togglePopout("network");
            compare(drawerState.popoutCurrentName, "");
            drawerState.togglePopout("network");
            compare(drawerState.popoutCurrentName, "network");
        }

        function test_toggle_popout_switches_to_other_name() {
            drawerState.togglePopout("network");
            drawerState.togglePopout("battery");
            compare(drawerState.popoutCurrentName, "battery");
            compare(drawerState.popoutCenterY, root.popoutCenterYByName.battery);
        }

        function test_clear_popout_drops_active_popout() {
            drawerState.showPopoutByName("bluetooth");
            drawerState.clearPopout();
            compare(drawerState.popoutCurrentName, "");
            verify(!drawerState.hasActivePopout);
        }

        function test_hide_popout_requests_hide_when_nothing_hovered() {
            drawerState.showPopoutByName("network");
            drawerState.hidePopout();
            compare(popoutHideRequestedSpy.count, 1);
        }

        function test_hide_popout_is_suppressed_while_popout_hovered() {
            drawerState.showPopoutByName("network");
            drawerState.setPopoutHovered(true);
            drawerState.hidePopout();
            compare(popoutHideRequestedSpy.count, 0);
        }

        function test_hide_popout_is_suppressed_while_icon_hovered() {
            drawerState.showPopoutByName("network");
            drawerState.popoutIconHovered = true;
            drawerState.hidePopout();
            compare(popoutHideRequestedSpy.count, 0);
        }
    }
}
