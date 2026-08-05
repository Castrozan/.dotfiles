import QtQuick
import ".."

Rectangle {
    id: statusIconRoot

    required property string iconText
    required property color iconColor
    property string popoutName: ""
    property var screenScope: null
    readonly property bool isHovered: statusIconMouseArea.containsMouse

    signal clicked()

    radius: 6
    color: statusIconMouseArea.containsMouse ? ThemeColors.surfaceTranslucent : "transparent"

    Text {
        anchors.centerIn: parent
        text: statusIconRoot.iconText
        font.pixelSize: 16
        font.family: "JetBrainsMono Nerd Font"
        color: statusIconRoot.iconColor

        Behavior on color {
            ColorAnimation { duration: 150 }
        }
    }

    MouseArea {
        id: statusIconMouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: statusIconRoot.clicked()
        onContainsMouseChanged: {
            if (containsMouse && statusIconRoot.screenScope && statusIconRoot.popoutName !== "") {
                let scenePos = statusIconRoot.mapToItem(null, 0, statusIconRoot.height / 2);
                statusIconRoot.screenScope.showPopout(statusIconRoot.popoutName, scenePos.y);
            }
        }
    }
}
