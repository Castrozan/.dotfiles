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

    Rectangle {
        id: popoutOuterBorder
        anchors.fill: parent
        radius: 24
        color: ThemeColors.primary
        visible: popoutWrapperRoot.hasContent

        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 24
            color: ThemeColors.primary
        }

        Rectangle {
            id: popoutInnerFill
            anchors.fill: parent
            anchors.topMargin: 1
            anchors.rightMargin: 1
            anchors.bottomMargin: 1
            anchors.leftMargin: 0
            radius: 23
            color: ThemeColors.background

            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: 23
                color: ThemeColors.background
            }
        }
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
