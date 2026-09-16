import QtQuick
import QtQuick.Layouts
import "../../dashboard"
import "../../dashboard/components"

RowLayout {
    id: notificationHeaderRoot
    required property bool showingHistory
    required property int notificationCount
    signal clearRequested

    Layout.fillWidth: true
    spacing: Appearance.spacing.small

    MaterialIcon {
        text: "notifications"
        color: Colours.palette.m3primary
        font.pointSize: Appearance.font.size.extraLarge
    }

    StyledText {
        Layout.fillWidth: true
        text: notificationHeaderRoot.showingHistory ? "History" : "Notifications"
        font.pointSize: Appearance.font.size.normal
        font.bold: true
        color: Colours.palette.m3onSurface
    }

    StyledText {
        visible: notificationHeaderRoot.notificationCount > 0
        text: notificationHeaderRoot.notificationCount
        font.pointSize: Appearance.font.size.smaller
        color: Colours.palette.m3onSurfaceVariant

        StyledRect {
            anchors.fill: parent
            anchors.margins: -4
            z: -1
            color: Colours.palette.m3surfaceContainerHighest
            radius: Appearance.rounding.full
        }
    }

    IconButton {
        visible: notificationHeaderRoot.notificationCount > 0
        implicitWidth: 28
        implicitHeight: 28
        icon: "clear_all"
        type: IconButton.Text
        font.pointSize: Appearance.font.size.normal

        onClicked: notificationHeaderRoot.clearRequested()
    }
}
