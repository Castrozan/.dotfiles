import QtQuick

Rectangle {
    id: playbackControlButtonRoot

    property string iconText: ""
    property bool isEnabled: true

    signal clicked()

    width: 40
    height: 40
    radius: 20
    color: {
        if (!isEnabled) return "transparent";
        if (controlButtonMouseArea.containsMouse) return ThemeColors.surfaceTranslucent;
        return "transparent";
    }
    opacity: isEnabled ? 1.0 : 0.3

    Text {
        anchors.centerIn: parent
        text: playbackControlButtonRoot.iconText
        font.pixelSize: 20
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    MouseArea {
        id: controlButtonMouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: playbackControlButtonRoot.isEnabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: {
            if (playbackControlButtonRoot.isEnabled)
                playbackControlButtonRoot.clicked();
        }
    }

    Behavior on color {
        ColorAnimation { duration: 150 }
    }
}
