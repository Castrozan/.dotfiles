import Quickshell
import QtQuick

Region {
    id: drawerInputMaskRoot

    required property int barTotalWidth
    required property real windowWidth
    required property real windowHeight
    required property int shapeJunctionRadius
    required property Item popoutItem
    required property Item dashboardItem
    required property Item launcherItem
    required property Item sessionItem
    required property Item utilitiesItem
    required property Item osdItem
    required property Item sidebarItem

    x: drawerInputMaskRoot.barTotalWidth
    y: 0
    width: drawerInputMaskRoot.windowWidth - drawerInputMaskRoot.barTotalWidth
    height: drawerInputMaskRoot.windowHeight
    intersection: Intersection.Xor

    regions: [
        Region {
            x: drawerInputMaskRoot.barTotalWidth
            y: 0
            width: drawerInputMaskRoot.windowWidth - drawerInputMaskRoot.barTotalWidth
            height: drawerInputMaskRoot.barTotalWidth / 3
            intersection: Intersection.Subtract
        },
        Region {
            x: drawerInputMaskRoot.barTotalWidth
            y: drawerInputMaskRoot.windowHeight - drawerInputMaskRoot.barTotalWidth / 3
            width: drawerInputMaskRoot.windowWidth - drawerInputMaskRoot.barTotalWidth
            height: drawerInputMaskRoot.barTotalWidth / 3
            intersection: Intersection.Subtract
        },
        Region {
            x: drawerInputMaskRoot.windowWidth - drawerInputMaskRoot.barTotalWidth / 3
            y: drawerInputMaskRoot.barTotalWidth / 3
            width: drawerInputMaskRoot.barTotalWidth / 3
            height: drawerInputMaskRoot.windowHeight - drawerInputMaskRoot.barTotalWidth * 2 / 3
            intersection: Intersection.Subtract
        },
        Region {
            x: drawerInputMaskRoot.popoutItem.x
            y: drawerInputMaskRoot.popoutItem.visible ? drawerInputMaskRoot.popoutItem.y - drawerInputMaskRoot.shapeJunctionRadius : 0
            width: drawerInputMaskRoot.popoutItem.visible ? drawerInputMaskRoot.popoutItem.width : 0
            height: drawerInputMaskRoot.popoutItem.visible ? drawerInputMaskRoot.popoutItem.height + drawerInputMaskRoot.shapeJunctionRadius * 2 : 0
            intersection: Intersection.Subtract
        },
        Region {
            x: drawerInputMaskRoot.dashboardItem.x
            y: drawerInputMaskRoot.dashboardItem.visible ? drawerInputMaskRoot.dashboardItem.y : 0
            width: drawerInputMaskRoot.dashboardItem.visible ? drawerInputMaskRoot.dashboardItem.width : 0
            height: drawerInputMaskRoot.dashboardItem.visible ? drawerInputMaskRoot.dashboardItem.height : 0
            intersection: Intersection.Subtract
        },
        Region {
            x: drawerInputMaskRoot.launcherItem.x
            y: drawerInputMaskRoot.launcherItem.visible ? drawerInputMaskRoot.launcherItem.y : 0
            width: drawerInputMaskRoot.launcherItem.visible ? drawerInputMaskRoot.launcherItem.width : 0
            height: drawerInputMaskRoot.launcherItem.visible ? drawerInputMaskRoot.launcherItem.height : 0
            intersection: Intersection.Subtract
        },
        Region {
            x: drawerInputMaskRoot.sessionItem.visible ? drawerInputMaskRoot.sessionItem.x : 0
            y: drawerInputMaskRoot.sessionItem.visible ? drawerInputMaskRoot.sessionItem.y : 0
            width: drawerInputMaskRoot.sessionItem.visible ? drawerInputMaskRoot.sessionItem.width : 0
            height: drawerInputMaskRoot.sessionItem.visible ? drawerInputMaskRoot.sessionItem.height : 0
            intersection: Intersection.Subtract
        },
        Region {
            x: drawerInputMaskRoot.utilitiesItem.visible ? drawerInputMaskRoot.utilitiesItem.x : 0
            y: drawerInputMaskRoot.utilitiesItem.visible ? drawerInputMaskRoot.utilitiesItem.y : 0
            width: drawerInputMaskRoot.utilitiesItem.visible ? drawerInputMaskRoot.utilitiesItem.width : 0
            height: drawerInputMaskRoot.utilitiesItem.visible ? drawerInputMaskRoot.utilitiesItem.height : 0
            intersection: Intersection.Subtract
        },
        Region {
            x: drawerInputMaskRoot.osdItem.visible ? drawerInputMaskRoot.osdItem.x : 0
            y: drawerInputMaskRoot.osdItem.visible ? drawerInputMaskRoot.osdItem.y : 0
            width: drawerInputMaskRoot.osdItem.visible ? drawerInputMaskRoot.osdItem.width : 0
            height: drawerInputMaskRoot.osdItem.visible ? drawerInputMaskRoot.osdItem.height : 0
            intersection: Intersection.Subtract
        },
        Region {
            x: drawerInputMaskRoot.sidebarItem.visible ? drawerInputMaskRoot.sidebarItem.x : 0
            y: drawerInputMaskRoot.sidebarItem.visible ? drawerInputMaskRoot.sidebarItem.y : 0
            width: drawerInputMaskRoot.sidebarItem.visible ? drawerInputMaskRoot.sidebarItem.width : 0
            height: drawerInputMaskRoot.sidebarItem.visible ? drawerInputMaskRoot.sidebarItem.height : 0
            intersection: Intersection.Subtract
        }
    ]
}
