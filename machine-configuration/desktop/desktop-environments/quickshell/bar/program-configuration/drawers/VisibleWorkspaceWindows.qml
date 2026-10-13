import QtQuick

QtObject {
    required property int monitorId
    required property int workspaceId
    required property int specialWorkspaceId
    property var clients: null

    readonly property bool hasWindowData: Array.isArray(clients) && monitorId >= 0 && workspaceId !== 0
    readonly property var visibleClients: hasWindowData ? clients.filter(client => client.mapped && !client.hidden && client.monitor === monitorId && (client.workspace.id === workspaceId || (specialWorkspaceId !== 0 && client.workspace.id === specialWorkspaceId) || client.pinned)) : []
    readonly property bool isEmpty: hasWindowData && visibleClients.length === 0
    readonly property bool hasFullscreenWindow: visibleClients.some(client => client.fullscreen === 2)
}
