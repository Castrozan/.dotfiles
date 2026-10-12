import QtQuick

QtObject {
    required property real windowWidth
    required property real windowHeight

    readonly property int triggerThickness: 1
    readonly property real innerWidth: Math.max(0, windowWidth - triggerThickness * 2)
    readonly property real innerHeight: Math.max(0, windowHeight - triggerThickness * 2)
    readonly property int rightZoneHeight: Math.floor(innerHeight / 3)

    readonly property rect leftTrigger: Qt.rect(0, triggerThickness, triggerThickness, innerHeight)
    readonly property rect topTrigger: Qt.rect(triggerThickness, 0, innerWidth, triggerThickness)
    readonly property rect bottomTrigger: Qt.rect(triggerThickness, windowHeight - triggerThickness, innerWidth, triggerThickness)
    readonly property rect sidebarTrigger: Qt.rect(windowWidth - triggerThickness, triggerThickness, triggerThickness, rightZoneHeight)
    readonly property rect osdTrigger: Qt.rect(windowWidth - triggerThickness, triggerThickness + rightZoneHeight, triggerThickness, innerHeight - rightZoneHeight * 2)
    readonly property rect sessionTrigger: Qt.rect(windowWidth - triggerThickness, windowHeight - triggerThickness - rightZoneHeight, triggerThickness, rightZoneHeight)
}
