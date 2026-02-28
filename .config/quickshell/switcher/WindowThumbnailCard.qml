import Quickshell
import Quickshell.Wayland
import QtQuick

Item {
    id: thumbnailCard

    required property var toplevelHandle
    required property string windowTitle
    required property string windowClass
    required property bool isSelected
    required property color accentColor
    required property color backgroundColor
    required property color foregroundColor

    readonly property int cardWidth: 330
    readonly property int cardHeight: 270
    readonly property int thumbnailHeight: 220
    readonly property int borderWidth: 4
    readonly property int cornerRadius: 16
    readonly property int iconSize: 20

    width: cardWidth
    height: cardHeight

    Rectangle {
        id: cardBackground
        anchors.fill: parent
        radius: cornerRadius
        color: backgroundColor
        border.color: isSelected ? accentColor : "transparent"
        border.width: borderWidth

        Rectangle {
            id: thumbnailContainer
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: borderWidth + 2
            height: thumbnailHeight - borderWidth
            radius: cornerRadius - 2
            color: Qt.rgba(0, 0, 0, 0.3)
            clip: true

            Loader {
                id: screencopyLoader
                anchors.fill: parent
                active: !!toplevelHandle

                sourceComponent: ScreencopyView {
                    anchors.fill: parent
                    captureSource: toplevelHandle
                    live: false
                    paintCursor: false

                    constraintSize: Qt.size(thumbnailContainer.width, thumbnailContainer.height)

                    Component.onCompleted: captureFrame()
                }
            }
        }

        Row {
            id: titleRow
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: 8
            spacing: 6

            Image {
                id: appIcon
                width: iconSize
                height: iconSize
                anchors.verticalCenter: parent.verticalCenter
                source: Quickshell.iconPath(windowClass.toLowerCase(), true)
                visible: status === Image.Ready
                sourceSize: Qt.size(iconSize, iconSize)
                smooth: true
            }

            Text {
                id: titleLabel
                anchors.verticalCenter: parent.verticalCenter
                width: Math.min(implicitWidth, cardWidth - iconSize - titleRow.spacing - 24)

                text: windowTitle
                color: foregroundColor
                font.pixelSize: 14
                font.bold: isSelected
                elide: Text.ElideRight
            }
        }
    }
}
