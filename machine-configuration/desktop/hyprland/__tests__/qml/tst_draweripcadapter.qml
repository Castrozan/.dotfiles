import QtQuick
import QtTest
import "../../../quickshell/bar/program-configuration"

Item {
    id: root

    QtObject {
        id: intentLog

        property string lastIntent: ""
    }

    QtObject {
        id: recordedDrawerState

        function toggleDashboard() {
            intentLog.lastIntent = "toggleDashboard";
        }

        function toggleLauncher() {
            intentLog.lastIntent = "toggleLauncher";
        }

        function toggleSession() {
            intentLog.lastIntent = "toggleSession";
        }

        function toggleUtilities() {
            intentLog.lastIntent = "toggleUtilities";
        }

        function toggleSidebar() {
            intentLog.lastIntent = "toggleSidebar";
        }

        function closeOsd() {
            intentLog.lastIntent = "closeOsd";
        }

        function togglePopout(name) {
            intentLog.lastIntent = "togglePopout:" + name;
        }

        function showPopoutByName(name) {
            intentLog.lastIntent = "showPopoutByName:" + name;
        }

        function clearPopout() {
            intentLog.lastIntent = "clearPopout";
        }
    }

    QtObject {
        id: recordedHoverController

        function showOsdTemporarily() {
            intentLog.lastIntent = "showOsdTemporarily";
        }
    }

    DrawerIpcAdapter {
        id: ipcAdapter

        drawerState: recordedDrawerState
        drawerHoverController: recordedHoverController
    }

    TestCase {
        name: "DrawerIpcAdapterTargets"

        function init() {
            intentLog.lastIntent = "";
        }

        function handlerForTarget(targetName) {
            for (var index = 0; index < ipcAdapter.data.length; index++) {
                if (ipcAdapter.data[index].target === targetName)
                    return ipcAdapter.data[index];
            }
            return null;
        }

        function test_every_recorded_target_is_registered_data() {
            return ["dashboard", "launcher", "session", "utilities", "sidebar", "osd", "popout"].map(target => ({ tag: target, target: target }));
        }

        function test_every_recorded_target_is_registered(data) {
            verify(handlerForTarget(data.target) !== null);
        }

        function test_panel_toggle_maps_onto_the_drawer_intent_data() {
            return [
                { tag: "dashboard", target: "dashboard", intent: "toggleDashboard" },
                { tag: "launcher", target: "launcher", intent: "toggleLauncher" },
                { tag: "session", target: "session", intent: "toggleSession" },
                { tag: "utilities", target: "utilities", intent: "toggleUtilities" },
                { tag: "sidebar", target: "sidebar", intent: "toggleSidebar" }
            ];
        }

        function test_panel_toggle_maps_onto_the_drawer_intent(data) {
            handlerForTarget(data.target).toggle();
            compare(intentLog.lastIntent, data.intent);
        }

        function test_osd_show_maps_onto_the_temporary_osd_intent() {
            handlerForTarget("osd").show();
            compare(intentLog.lastIntent, "showOsdTemporarily");
        }

        function test_osd_hide_maps_onto_the_close_intent() {
            handlerForTarget("osd").hide();
            compare(intentLog.lastIntent, "closeOsd");
        }

        function test_popout_toggle_forwards_the_name() {
            handlerForTarget("popout").toggle("bluetooth");
            compare(intentLog.lastIntent, "togglePopout:bluetooth");
        }

        function test_popout_show_forwards_the_name() {
            handlerForTarget("popout").show("statusicons");
            compare(intentLog.lastIntent, "showPopoutByName:statusicons");
        }

        function test_popout_hide_maps_onto_the_clear_intent() {
            handlerForTarget("popout").hide();
            compare(intentLog.lastIntent, "clearPopout");
        }
    }
}
