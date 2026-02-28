import QtQuick
import ".."

Item {
    id: popoutWrapperRoot

    required property string currentName
    required property real currentCenterY
    required property real screenHeight

    property bool containsMouse: popoutMouseArea.containsMouse

    readonly property bool hasContent: currentName !== ""
    readonly property real popoutHeight: popoutContent.implicitHeight + 32
    readonly property real popoutWidth: hasContent ? popoutContent.implicitWidth + 32 : 0
    readonly property real clampedY: Math.max(0, Math.min(currentCenterY - popoutHeight / 2, screenHeight - popoutHeight))

    y: clampedY
    width: popoutWidth
    height: hasContent ? popoutHeight : 0
    visible: hasContent

    Behavior on y {
        NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
    }

    MouseArea {
        id: popoutMouseArea
        anchors.fill: parent
        hoverEnabled: true
        propagateComposedEvents: true
        onClicked: mouse => mouse.accepted = false
        onPressed: mouse => mouse.accepted = false
        onReleased: mouse => mouse.accepted = false
    }

    PopoutContent {
        id: popoutContent
        anchors.fill: parent
        anchors.margins: 16
        currentName: popoutWrapperRoot.currentName
    }
}
