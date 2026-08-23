import QtQuick
import QtTest
import "../../../quickshell/bar/program-configuration"

Item {
    id: root

    readonly property var drawerNames: ["dashboard", "launcher", "session", "utilities", "sidebar", "osd"]
    readonly property int drivenInterval: 10
    readonly property int drivenTimeout: 400
    readonly property int osdAutoHideElapsed: 2200

    QtObject {
        id: fakePopoutAnchors

        function centerYForPopout(name) {
            return 42;
        }
    }

    DrawerState {
        id: recordedIntervalState

        popoutAnchorResolver: fakePopoutAnchors
    }

    DrawerHoverController {
        id: recordedIntervalController

        drawerState: recordedIntervalState
    }

    DrawerState {
        id: drawerState

        popoutAnchorResolver: fakePopoutAnchors
    }

    DrawerHoverController {
        id: hoverController

        drawerState: drawerState
    }

    TestCase {
        name: "DrawerHoverControllerRecordedIntervals"

        function test_conceal_delay_matches_recorded_interval_data() {
            return root.drawerNames.map(name => ({ tag: name, drawer: name }));
        }

        function test_conceal_delay_matches_recorded_interval(data) {
            compare(recordedIntervalController[data.drawer].concealDelayInterval, 450);
        }

        function test_reveal_delay_matches_recorded_interval_data() {
            return ["dashboard", "session", "sidebar", "osd"].map(name => ({ tag: name, drawer: name }));
        }

        function test_reveal_delay_matches_recorded_interval(data) {
            compare(recordedIntervalController[data.drawer].revealDelayInterval, 200);
        }

        function test_launcher_reveals_without_delay() {
            compare(recordedIntervalController.launcher.revealDelayInterval, 0);
        }
    }

    TestCase {
        name: "DrawerHoverControllerPanelSequences"

        function init() {
            for (var index = 0; index < root.drawerNames.length; index++) {
                var drawerName = root.drawerNames[index];
                var timing = hoverController[drawerName];
                timing.triggerHovered = false;
                timing.revealDelayInterval = drawerName === "launcher" ? 0 : root.drivenInterval;
                timing.concealDelayInterval = root.drivenInterval;
                drawerState[drawerName + "Hovered"] = false;
            }
            drawerState.closeAllPanels();
            drawerState.closeOsd();
            wait(root.drivenInterval * 4);
        }

        function test_trigger_enter_reveals_after_the_delay() {
            hoverController.dashboard.triggerEntered();
            verify(!drawerState.dashboardVisible);
            tryVerify(() => drawerState.dashboardVisible, root.drivenTimeout);
        }

        function test_trigger_leave_cancels_a_pending_reveal() {
            hoverController.session.triggerEntered();
            hoverController.session.triggerLeft();
            wait(root.drivenInterval * 4);
            verify(!drawerState.sessionVisible);
        }

        function test_trigger_leave_conceals_after_the_delay() {
            hoverController.sidebar.triggerEntered();
            tryVerify(() => drawerState.sidebarVisible, root.drivenTimeout);
            hoverController.sidebar.triggerLeft();
            tryVerify(() => !drawerState.sidebarVisible, root.drivenTimeout);
        }

        function test_content_hover_records_state_and_holds_the_drawer_open() {
            hoverController.dashboard.triggerEntered();
            tryVerify(() => drawerState.dashboardVisible, root.drivenTimeout);
            hoverController.dashboard.contentEntered();
            verify(drawerState.dashboardHovered);
            hoverController.dashboard.triggerLeft();
            wait(root.drivenInterval * 4);
            verify(drawerState.dashboardVisible);
        }

        function test_content_leave_conceals_the_drawer() {
            hoverController.dashboard.triggerEntered();
            tryVerify(() => drawerState.dashboardVisible, root.drivenTimeout);
            hoverController.dashboard.contentEntered();
            hoverController.dashboard.triggerLeft();
            hoverController.dashboard.contentLeft();
            verify(!drawerState.dashboardHovered);
            tryVerify(() => !drawerState.dashboardVisible, root.drivenTimeout);
        }

        function test_launcher_trigger_enter_reveals_without_waiting() {
            hoverController.launcher.triggerEntered();
            verify(drawerState.launcherVisible);
        }

        function test_utilities_trigger_never_reveals() {
            hoverController.utilities.triggerEntered();
            wait(root.drivenInterval * 4);
            verify(!drawerState.utilitiesVisible);
        }

        function test_utilities_content_leave_conceals_without_a_trigger() {
            drawerState.toggleUtilities();
            hoverController.utilities.contentEntered();
            hoverController.utilities.contentLeft();
            tryVerify(() => !drawerState.utilitiesVisible, root.drivenTimeout);
        }

        function test_osd_message_opens_and_auto_hides() {
            hoverController.showOsdTemporarily();
            verify(drawerState.osdVisible);
            tryVerify(() => !drawerState.osdVisible, root.osdAutoHideElapsed);
        }

        function test_osd_content_hover_cancels_the_auto_hide() {
            hoverController.showOsdTemporarily();
            hoverController.osd.contentEntered();
            verify(drawerState.osdHovered);
            wait(root.osdAutoHideElapsed);
            verify(drawerState.osdVisible);
        }
    }
}
