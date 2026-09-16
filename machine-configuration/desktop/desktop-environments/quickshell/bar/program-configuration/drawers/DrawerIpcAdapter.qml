import Quickshell.Io
import QtQuick

Item {
    id: drawerIpcAdapterRoot

    required property var drawerState
    required property var drawerHoverController

    IpcHandler {
        target: "dashboard"

        function toggle(): void {
            drawerIpcAdapterRoot.drawerState.toggleDashboard();
        }
    }

    IpcHandler {
        target: "launcher"

        function toggle(): void {
            drawerIpcAdapterRoot.drawerState.toggleLauncher();
        }
    }

    IpcHandler {
        target: "session"

        function toggle(): void {
            drawerIpcAdapterRoot.drawerState.toggleSession();
        }
    }

    IpcHandler {
        target: "utilities"

        function toggle(): void {
            drawerIpcAdapterRoot.drawerState.toggleUtilities();
        }
    }

    IpcHandler {
        target: "sidebar"

        function toggle(): void {
            drawerIpcAdapterRoot.drawerState.toggleSidebar();
        }
    }

    IpcHandler {
        target: "osd"

        function show(): void {
            drawerIpcAdapterRoot.drawerHoverController.showOsdTemporarily();
        }

        function hide(): void {
            drawerIpcAdapterRoot.drawerState.closeOsd();
        }
    }

    IpcHandler {
        target: "popout"

        function toggle(name: string): void {
            drawerIpcAdapterRoot.drawerState.togglePopout(name);
        }

        function show(name: string): void {
            drawerIpcAdapterRoot.drawerState.showPopoutByName(name);
        }

        function hide(): void {
            drawerIpcAdapterRoot.drawerState.clearPopout();
        }
    }
}
