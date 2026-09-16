import QtQuick

QtObject {
    id: aggregatedRightPanelGeometry

    required property Item sessionItem
    required property Item sidebarItem
    required property Item utilitiesItem
    required property Item osdItem

    readonly property bool hasSession: sessionItem.visible && sessionItem.width > 0
    readonly property bool hasSidebar: sidebarItem.visible && sidebarItem.width > 0
    readonly property bool hasUtilities: utilitiesItem.visible && utilitiesItem.height > 0
    readonly property bool hasOsd: osdItem.visible && osdItem.width > 0
    readonly property bool hasAnyRightPanel: hasSession || hasSidebar || hasUtilities || hasOsd

    readonly property real sessionTop: hasSession ? sessionItem.y : 99999
    readonly property real sessionBottom: hasSession ? sessionItem.y + sessionItem.height : 0
    readonly property real sidebarTop: hasSidebar ? sidebarItem.y : 99999
    readonly property real sidebarBottom: hasSidebar ? sidebarItem.y + sidebarItem.height : 0
    readonly property real utilitiesTop: hasUtilities ? utilitiesItem.y : 99999
    readonly property real utilitiesBottom: hasUtilities ? utilitiesItem.y + utilitiesItem.height : 0
    readonly property real osdTop: hasOsd ? osdItem.y : 99999
    readonly property real osdBottom: hasOsd ? osdItem.y + osdItem.height : 0

    readonly property real aggregatedY: hasAnyRightPanel ? Math.min(sessionTop, sidebarTop, utilitiesTop, osdTop) : 0
    readonly property real aggregatedBottom: hasAnyRightPanel ? Math.max(sessionBottom, sidebarBottom, utilitiesBottom, osdBottom) : 0
    readonly property real aggregatedHeight: hasAnyRightPanel ? aggregatedBottom - aggregatedY : 0
    readonly property real aggregatedWidth: hasAnyRightPanel ? Math.max(hasSession ? sessionItem.width + sidebarItem.width : 0, hasSidebar ? sidebarItem.width : 0, hasUtilities ? utilitiesItem.width : 0, hasOsd ? osdItem.width + (hasSession ? sessionItem.width : 0) + (hasSidebar ? sidebarItem.width : 0) : 0) : 0
}
