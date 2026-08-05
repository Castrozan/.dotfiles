import QtQuick
import QtQuick.Layouts
import ".."

Rectangle {
    id: statusIconsPopoutRowRoot

    property string rowIconText: ""
    property color rowIconColor: ThemeColors.foreground
    property real rowIconOpacity: 1.0
    property string rowLabel: ""
    property string rowStateText: ""
    property color rowStateColor: ThemeColors.dim

    signal rowClicked()

    Layout.fillWidth: true
    Layout.preferredHeight: 32

    radius: 6
    color: statusIconsPopoutRowMouseArea.containsMouse ? ThemeColors.surfaceTranslucent : "transparent"

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 12
        spacing: 12

        Text {
            text: statusIconsPopoutRowRoot.rowIconText
            font.pixelSize: 18
            font.family: "JetBrainsMono Nerd Font"
            color: statusIconsPopoutRowRoot.rowIconColor
            opacity: statusIconsPopoutRowRoot.rowIconOpacity
            Layout.preferredWidth: 24
            horizontalAlignment: Text.AlignHCenter

            Behavior on color {
                ColorAnimation { duration: 150 }
            }
            Behavior on opacity {
                NumberAnimation { duration: 150 }
            }
        }

        Text {
            text: statusIconsPopoutRowRoot.rowLabel
            font.pixelSize: 13
            font.family: "JetBrainsMono Nerd Font"
            color: ThemeColors.foreground
            Layout.fillWidth: true
            elide: Text.ElideRight
        }

        Text {
            text: statusIconsPopoutRowRoot.rowStateText
            font.pixelSize: 11
            font.family: "JetBrainsMono Nerd Font"
            color: statusIconsPopoutRowRoot.rowStateColor
            visible: text !== ""
        }
    }

    MouseArea {
        id: statusIconsPopoutRowMouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: statusIconsPopoutRowRoot.rowClicked()
    }
}
