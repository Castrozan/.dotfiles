import QtQuick
import QtTest

DrawerStateFixture {
    id: root

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
}
