import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/drawers"

Item {
    id: root

    readonly property var popoutCenterYByName: ({
            network: 110,
            bluetooth: 220,
            battery: 330,
            statusicons: 440
        })

    readonly property var panelToggleCases: [
        {
            tag: "dashboard",
            toggle: "toggleDashboard",
            visible: "dashboardVisible"
        },
        {
            tag: "launcher",
            toggle: "toggleLauncher",
            visible: "launcherVisible"
        },
        {
            tag: "session",
            toggle: "toggleSession",
            visible: "sessionVisible"
        },
        {
            tag: "utilities",
            toggle: "toggleUtilities",
            visible: "utilitiesVisible"
        },
        {
            tag: "sidebar",
            toggle: "toggleSidebar",
            visible: "sidebarVisible"
        }
    ]

    readonly property var popoutNameCases: [
        {
            tag: "network",
            name: "network"
        },
        {
            tag: "bluetooth",
            name: "bluetooth"
        },
        {
            tag: "battery",
            name: "battery"
        },
        {
            tag: "statusicons",
            name: "statusicons"
        }
    ]

    property QtObject fakePopoutAnchors: QtObject {
        id: fakePopoutAnchors

        function centerYForPopout(name) {
            var centerY = root.popoutCenterYByName[name];
            return centerY === undefined ? -1 : centerY;
        }
    }

    property DrawerState drawerState: DrawerState {
        id: drawerState

        popoutAnchorResolver: fakePopoutAnchors
    }

    property SignalSpy popoutShownSpy: SignalSpy {
        id: popoutShownSpy

        target: drawerState
        signalName: "popoutShown"
    }

    property SignalSpy popoutHideRequestedSpy: SignalSpy {
        id: popoutHideRequestedSpy

        target: drawerState
        signalName: "popoutHideRequested"
    }
}
