import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/drawers"

TestCase {
    name: "VisibleWorkspaceWindows"

    VisibleWorkspaceWindows {
        id: workspaceWindows
        monitorId: 0
        workspaceId: 1
        specialWorkspaceId: 0
    }

    function client(workspaceId, settings = {}) {
        return Object.assign({
            workspace: {
                id: workspaceId
            },
            monitor: 0,
            mapped: true,
            hidden: false,
            pinned: false,
            fullscreen: 0
        }, settings);
    }

    function init() {
        workspaceWindows.monitorId = 0;
        workspaceWindows.workspaceId = 1;
        workspaceWindows.specialWorkspaceId = 0;
        workspaceWindows.clients = null;
    }

    function test_visible_windows_data() {
        return [
            {
                tag: "empty",
                clients: [],
                empty: true
            },
            {
                tag: "unknown",
                clients: null,
                empty: false
            },
            {
                tag: "malformed",
                clients: {},
                empty: false
            },
            {
                tag: "regular",
                clients: [client(1)],
                empty: false
            },
            {
                tag: "floating",
                clients: [client(1, {
                        floating: true
                    })],
                empty: false
            },
            {
                tag: "other_workspace",
                clients: [client(2)],
                empty: true
            },
            {
                tag: "hidden",
                clients: [client(1, {
                        hidden: true
                    })],
                empty: true
            },
            {
                tag: "unmapped",
                clients: [client(1, {
                        mapped: false
                    })],
                empty: true
            },
            {
                tag: "pinned",
                clients: [client(2, {
                        pinned: true
                    })],
                empty: false
            },
            {
                tag: "other_monitor_pinned",
                clients: [client(2, {
                        pinned: true,
                        monitor: 1
                    })],
                empty: true
            },
            {
                tag: "closed_special",
                clients: [client(-98)],
                empty: true
            },
            {
                tag: "visible_special",
                clients: [client(-98)],
                specialWorkspaceId: -98,
                empty: false
            },
            {
                tag: "empty_special",
                clients: [],
                specialWorkspaceId: -98,
                empty: true
            },
            {
                tag: "named_workspace",
                clients: [client(-5)],
                workspaceId: -5,
                empty: false
            },
            {
                tag: "unknown_workspace",
                clients: [],
                workspaceId: 0,
                empty: false
            },
            {
                tag: "unknown_monitor",
                clients: [],
                monitorId: -1,
                empty: false
            }
        ];
    }

    function test_visible_windows(data) {
        workspaceWindows.workspaceId = data.workspaceId ?? 1;
        workspaceWindows.monitorId = data.monitorId ?? 0;
        workspaceWindows.specialWorkspaceId = data.specialWorkspaceId ?? 0;
        workspaceWindows.clients = data.clients;
        compare(workspaceWindows.isEmpty, data.empty);
    }

    function test_open_close_move_and_special_workspace_changes() {
        workspaceWindows.clients = [];
        compare(workspaceWindows.isEmpty, true);
        workspaceWindows.clients = [client(1)];
        compare(workspaceWindows.isEmpty, false);
        workspaceWindows.workspaceId = 2;
        compare(workspaceWindows.isEmpty, true);
        workspaceWindows.clients = [client(2)];
        compare(workspaceWindows.isEmpty, false);
        workspaceWindows.clients = [client(-98)];
        compare(workspaceWindows.isEmpty, true);
        workspaceWindows.specialWorkspaceId = -98;
        compare(workspaceWindows.isEmpty, false);
        workspaceWindows.specialWorkspaceId = 0;
        compare(workspaceWindows.isEmpty, true);
        workspaceWindows.clients = null;
        compare(workspaceWindows.isEmpty, false);
    }

    function test_fullscreen_only_on_visible_workspace() {
        workspaceWindows.clients = [client(2, {
                fullscreen: 2
            }), client(1, {
                fullscreen: 1
            })];
        compare(workspaceWindows.hasFullscreenWindow, false);
        workspaceWindows.workspaceId = 2;
        compare(workspaceWindows.hasFullscreenWindow, true);
        workspaceWindows.clients = [];
        compare(workspaceWindows.hasFullscreenWindow, false);
    }
}
