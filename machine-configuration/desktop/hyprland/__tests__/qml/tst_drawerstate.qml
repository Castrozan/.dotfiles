import QtQuick
import QtTest
import "../../../quickshell/bar/program-configuration"

Item {
    id: root

    readonly property var popoutCenterYByName: ({
        network: 110,
        bluetooth: 220,
        battery: 330,
        statusicons: 440
    })

    readonly property var panelToggleCases: [
        { tag: "dashboard", toggle: "toggleDashboard", visible: "dashboardVisible" },
        { tag: "launcher", toggle: "toggleLauncher", visible: "launcherVisible" },
        { tag: "session", toggle: "toggleSession", visible: "sessionVisible" },
        { tag: "utilities", toggle: "toggleUtilities", visible: "utilitiesVisible" },
        { tag: "sidebar", toggle: "toggleSidebar", visible: "sidebarVisible" }
    ]

    readonly property var popoutNameCases: [
        { tag: "network", name: "network" },
        { tag: "bluetooth", name: "bluetooth" },
        { tag: "battery", name: "battery" },
        { tag: "statusicons", name: "statusicons" }
    ]

    QtObject {
        id: fakePopoutAnchors

        function centerYForPopout(name) {
            var centerY = root.popoutCenterYByName[name];
            return centerY === undefined ? -1 : centerY;
        }
    }

    DrawerState {
        id: drawerState

        popoutAnchorResolver: fakePopoutAnchors
    }

    SignalSpy {
        id: popoutShownSpy

        target: drawerState
        signalName: "popoutShown"
    }

    SignalSpy {
        id: popoutHideRequestedSpy

        target: drawerState
        signalName: "popoutHideRequested"
    }

    TestCase {
        name: "DrawerStatePanelToggles"

        function init() {
            drawerState.closeAllPanels();
            drawerState.closeOsd();
        }

        function test_toggle_from_hidden_shows_data() {
            return root.panelToggleCases;
        }

        function test_toggle_from_hidden_shows(data) {
            compare(drawerState[data.visible], false);
            drawerState[data.toggle]();
            compare(drawerState[data.visible], true);
        }

        function test_toggle_from_visible_hides_data() {
            return root.panelToggleCases;
        }

        function test_toggle_from_visible_hides(data) {
            drawerState[data.toggle]();
            compare(drawerState[data.visible], true);
            drawerState[data.toggle]();
            compare(drawerState[data.visible], false);
        }

        function test_opening_one_panel_leaves_another_open() {
            drawerState.toggleDashboard();
            drawerState.toggleSidebar();
            verify(drawerState.dashboardVisible);
            verify(drawerState.sidebarVisible);
        }

        function test_has_any_panel_visible_tracks_every_panel_data() {
            return root.panelToggleCases;
        }

        function test_has_any_panel_visible_tracks_every_panel(data) {
            verify(!drawerState.hasAnyPanelVisible);
            drawerState[data.toggle]();
            verify(drawerState.hasAnyPanelVisible);
        }

        function test_osd_visibility_stays_out_of_panel_aggregate() {
            drawerState.openOsd();
            verify(drawerState.osdVisible);
            verify(!drawerState.hasAnyPanelVisible);
        }

        function test_close_all_panels_hides_every_panel() {
            drawerState.toggleDashboard();
            drawerState.toggleLauncher();
            drawerState.toggleSession();
            drawerState.toggleUtilities();
            drawerState.toggleSidebar();
            drawerState.closeAllPanels();
            verify(!drawerState.hasAnyPanelVisible);
        }
    }

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
