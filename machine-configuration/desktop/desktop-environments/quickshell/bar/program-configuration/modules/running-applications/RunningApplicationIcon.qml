import Quickshell
import Qt5Compat.GraphicalEffects
import QtQuick
import "../.."

Rectangle {
    id: runningAppDelegate

    required property var application
    required property int cellSize
    required property string iconName
    required property bool focused

    signal activated

    width: cellSize
    height: cellSize

    radius: 6
    color: runningAppMouseArea.containsMouse ? ThemeColors.surfaceTranslucent : "transparent"

    Image {
        id: runningAppIcon
        anchors.centerIn: parent
        width: 16
        height: 16
        source: Quickshell.iconPath(runningAppDelegate.iconName, true)
        sourceSize: Qt.size(16, 16)
        smooth: true
        visible: status === Image.Ready
    }

    Colorize {
        anchors.fill: runningAppIcon
        source: runningAppIcon
        visible: runningAppIcon.visible
        hue: ThemeColors.foreground.hslHue
        saturation: ThemeColors.foreground.hslSaturation
        lightness: 0.3
    }

    Text {
        anchors.centerIn: parent
        visible: runningAppIcon.status !== Image.Ready
        text: runningAppDelegate.application.windowClass.charAt(0).toUpperCase()
        font.pixelSize: 14
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    Rectangle {
        id: focusedAppAccentIndicator
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: -2
        width: 3
        height: runningAppDelegate.focused ? 12 : 4
        radius: 1.5
        color: ThemeColors.accent

        Behavior on height {
            NumberAnimation {
                duration: 150
                easing.type: Easing.OutQuad
            }
        }
    }

    MouseArea {
        id: runningAppMouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        onClicked: {
            runningAppDelegate.activated();
        }
    }
}
