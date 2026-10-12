import Quickshell
import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/drawers"

Item {
    ScreenEdgeGeometry {
        id: edgeGeometry
        windowWidth: 1920
        windowHeight: 1080
    }

    Item {
        id: hiddenPanel
        visible: false
    }

    Item {
        id: panel
        x: 400
        y: 200
        width: 300
        height: 180
        visible: false
    }

    DrawerInputMask {
        id: inputMask
        edgeGeometry: edgeGeometry
        leftBarWidth: 0
        shapeJunctionRadius: 36
        popoutItem: hiddenPanel
        dashboardItem: hiddenPanel
        launcherItem: hiddenPanel
        sessionItem: hiddenPanel
        utilitiesItem: hiddenPanel
        osdItem: hiddenPanel
        sidebarItem: hiddenPanel
    }

    TestCase {
        name: "FramelessDrawerInputMask"
        readonly property var panelProperties: ["popoutItem", "dashboardItem", "launcherItem", "sessionItem", "utilitiesItem", "osdItem", "sidebarItem"]

        function init() {
            edgeGeometry.windowWidth = 1920;
            edgeGeometry.windowHeight = 1080;
            inputMask.leftBarWidth = 0;
            panel.visible = false;
            for (const property of panelProperties)
                inputMask[property] = hiddenPanel;
        }

        function acceptsPoint(x, y) {
            compare(inputMask.width, 0);
            compare(inputMask.height, 0);
            compare(inputMask.intersection, Intersection.Combine);
            for (const region of inputMask.regions) {
                compare(region.intersection, Intersection.Combine);
                if (x >= region.x && x < region.x + region.width && y >= region.y && y < region.y + region.height)
                    return true;
            }
            return false;
        }

        function test_hidden_panels_leave_the_desktop_clickable() {
            verify(!acceptsPoint(960, 540));
            verify(!acceptsPoint(24, 550));
            verify(!acceptsPoint(1919, 540));
        }

        function test_edge_capture_is_one_pixel_wide_data() {
            return [["left-edge", 0, 400, true], ["left-inner", 1, 400, false], ["top-edge", 960, 0, true], ["top-inner", 960, 1, false], ["bottom-edge", 960, 1079, true], ["bottom-inner", 960, 1078, false], ["sidebar-edge", 1919, 100, true], ["sidebar-inner", 1918, 100, false], ["session-edge", 1919, 980, true], ["session-inner", 1918, 980, false], ["top-left-corner", 0, 0, false]].map(point => ({
                        tag: point[0],
                        x: point[1],
                        y: point[2],
                        captured: point[3]
                    }));
        }

        function test_edge_capture_is_one_pixel_wide(data) {
            compare(acceptsPoint(data.x, data.y), data.captured);
        }

        function test_revealed_bar_receives_input_until_concealed() {
            inputMask.leftBarWidth = 48;
            verify(acceptsPoint(24, 550));
            inputMask.leftBarWidth = 0;
            verify(!acceptsPoint(24, 550));
        }

        function test_visible_panel_receives_input_data() {
            return panelProperties.map(property => ({
                        tag: property,
                        property: property
                    }));
        }

        function test_visible_panel_receives_input(data) {
            inputMask[data.property] = panel;
            panel.visible = true;
            verify(acceptsPoint(410, 210));
            verify(!acceptsPoint(701, 210));
            panel.visible = false;
            verify(!acceptsPoint(410, 210));
        }

        function test_triggers_follow_monitor_dimensions() {
            edgeGeometry.windowWidth = 1280;
            edgeGeometry.windowHeight = 720;
            verify(acceptsPoint(1279, 100));
            verify(acceptsPoint(640, 719));
            verify(!acceptsPoint(1280, 100));
            verify(!acceptsPoint(640, 720));
        }
    }
}
