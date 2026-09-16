import QtQuick
import ".."

Rectangle {
    id: mprisPopoutControlButtonRoot

    property string iconText: ""
    property bool isEnabled: true

    signal clicked()

    width: 32
    height: 32
    radius: 16
    color: controlButtonMouseArea.containsMouse && isEnabled ? ThemeColors.surfaceTranslucent : "transparent"
    opacity: isEnabled ? 1.0 : 0.3

    Text {
        anchors.centerIn: parent
        text: mprisPopoutControlButtonRoot.iconText
        font.pixelSize: 16
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    MouseArea {
        id: controlButtonMouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: mprisPopoutControlButtonRoot.isEnabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: {
            if (mprisPopoutControlButtonRoot.isEnabled)
                mprisPopoutControlButtonRoot.clicked();
        }
    }
}
