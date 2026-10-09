import Quickshell

Scope {
    id: queries

    property bool active: true

    signal windowsReceived(var windows)
    signal monitorsReceived(var monitors)
    signal layersReceived(var layers)
    signal workspacesReceived(var workspaces)
    signal activeWorkspaceReceived(var workspace)

    function refresh(windows: bool, monitors: bool, layers: bool, workspaces: bool, activeWorkspace: bool): void {
        if (windows)
            getClients.refresh();
        if (monitors)
            getMonitors.refresh();
        if (layers)
            getLayers.refresh();
        if (workspaces)
            getWorkspaces.refresh();
        if (activeWorkspace)
            getActiveWorkspace.refresh();
    }

    HyprlandJsonQuery {
        id: getClients
        queryName: "clients"
        active: queries.active
        onResponseReceived: response => queries.windowsReceived(response)
    }

    HyprlandJsonQuery {
        id: getMonitors
        queryName: "monitors"
        active: queries.active
        onResponseReceived: response => queries.monitorsReceived(response)
    }

    HyprlandJsonQuery {
        id: getLayers
        queryName: "layers"
        active: queries.active
        onResponseReceived: response => queries.layersReceived(response)
    }

    HyprlandJsonQuery {
        id: getWorkspaces
        queryName: "workspaces"
        active: queries.active
        onResponseReceived: response => queries.workspacesReceived(response)
    }

    HyprlandJsonQuery {
        id: getActiveWorkspace
        queryName: "activeworkspace"
        active: queries.active
        onResponseReceived: response => queries.activeWorkspaceReceived(response)
    }
}
