pragma ComponentBehavior: Bound

import Quickshell.Io
import "../dashboard/components"
import "../dashboard"
import QtQuick
import QtQuick.Layouts

StyledRect {
    id: notificationItemRoot

    required property int notificationId
    required property string appName
    required property string summary
    required property string body
    required property int urgency
    property bool dismissable: true

    signal dismissed()

    implicitWidth: 280
    implicitHeight: notificationItemLayout.implicitHeight + Appearance.padding.normal * 2

    color: urgency >= 2 ? Colours.palette.m3errorContainer : Colours.palette.m3surfaceContainerHigh
    radius: Appearance.rounding.normal

    ColumnLayout {
        id: notificationItemLayout

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.margins: Appearance.padding.normal

        spacing: Appearance.spacing.smaller

        RowLayout {
            Layout.fillWidth: true
            spacing: Appearance.spacing.small

            StyledText {
                Layout.fillWidth: true
                text: notificationItemRoot.appName || "Unknown"
                font.pointSize: Appearance.font.size.smaller
                color: Qt.alpha(Colours.palette.m3onSurface, 0.6)
                elide: Text.ElideRight
            }

            IconButton {
                visible: notificationItemRoot.dismissable
                implicitWidth: 20
                implicitHeight: 20
                icon: "close"
                type: IconButton.Text
                font.pointSize: Appearance.font.size.small

                Process {
                    id: dismissNotificationProcess
                    command: ["makoctl", "dismiss", "-n", String(notificationItemRoot.notificationId)]
                    onRunningChanged: {
                        if (!running)
                            notificationItemRoot.dismissed();
                    }
                }

                onClicked: dismissNotificationProcess.running = true
            }
        }

        StyledText {
            Layout.fillWidth: true
            text: notificationItemRoot.summary
            font.pointSize: Appearance.font.size.small
            font.bold: true
            color: urgency >= 2 ? Colours.palette.m3onErrorContainer : Colours.palette.m3onSurface
            wrapMode: Text.WordWrap
            elide: Text.ElideRight
            maximumLineCount: 2
        }

        StyledText {
            Layout.fillWidth: true
            visible: notificationItemRoot.body !== ""
            text: notificationItemRoot.body
            font.pointSize: Appearance.font.size.smaller
            color: urgency >= 2 ? Colours.palette.m3onErrorContainer : Qt.alpha(Colours.palette.m3onSurface, 0.75)
            wrapMode: Text.WordWrap
            elide: Text.ElideRight
            maximumLineCount: 3
        }
    }
}
