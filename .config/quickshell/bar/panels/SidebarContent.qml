pragma ComponentBehavior: Bound

import Quickshell.Io
import "../dashboard/components"
import "../dashboard"
import QtQuick
import QtQuick.Layouts

Item {
    id: sidebarContentRoot

    property real availableHeight: 400
    property var activeNotificationsList: []
    property var historyNotificationsList: []
    property var notificationsList: activeNotificationsList.length > 0 ? activeNotificationsList : historyNotificationsList
    property bool showingHistory: activeNotificationsList.length === 0 && historyNotificationsList.length > 0

    implicitWidth: 300
    implicitHeight: Math.min(sidebarLayout.implicitHeight + Appearance.padding.large * 2, availableHeight)

    function extractNotificationsFromBusctlJson(jsonOutput: string): var {
        try {
            let raw = JSON.parse(jsonOutput);
            let parsed = [];
            for (let i = 0; i < raw.data.length; i++) {
                let group = raw.data[i];
                let items = Array.isArray(group) ? group : [group];
                for (let j = 0; j < items.length; j++) {
                    let notif = items[j];
                    parsed.push({
                        id: notif["id"] ? notif["id"].data : 0,
                        summary: notif["summary"] ? notif["summary"].data : "",
                        appName: notif["app-name"] ? notif["app-name"].data : "",
                        body: notif["body"] ? notif["body"].data : "",
                        urgency: notif["urgency"] ? notif["urgency"].data : 1
                    });
                }
            }
            return parsed;
        } catch (error) {
            return [];
        }
    }

    Process {
        id: activeNotificationsQueryProcess
        command: ["busctl", "--user", "--json=short", "call", "org.freedesktop.Notifications", "/fr/emersion/Mako", "fr.emersion.Mako", "ListNotifications"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                sidebarContentRoot.activeNotificationsList = sidebarContentRoot.extractNotificationsFromBusctlJson(data);
            }
        }
    }

    Process {
        id: historyNotificationsQueryProcess
        command: ["busctl", "--user", "--json=short", "call", "org.freedesktop.Notifications", "/fr/emersion/Mako", "fr.emersion.Mako", "ListHistory"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                sidebarContentRoot.historyNotificationsList = sidebarContentRoot.extractNotificationsFromBusctlJson(data);
            }
        }
    }

    Timer {
        id: notificationsPollTimer
        interval: 3000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            activeNotificationsQueryProcess.running = true;
            historyNotificationsQueryProcess.running = true;
        }
    }

    ColumnLayout {
        id: sidebarLayout

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: Appearance.padding.large

        spacing: Appearance.spacing.small

        RowLayout {
            Layout.fillWidth: true
            spacing: Appearance.spacing.small

            MaterialIcon {
                text: "notifications"
                color: Colours.palette.m3primary
                font.pointSize: Appearance.font.size.extraLarge
            }

            StyledText {
                Layout.fillWidth: true
                text: sidebarContentRoot.showingHistory ? "History" : "Notifications"
                font.pointSize: Appearance.font.size.normal
                font.bold: true
                color: Colours.palette.m3onSurface
            }

            StyledText {
                visible: sidebarContentRoot.notificationsList.length > 0
                text: sidebarContentRoot.notificationsList.length
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
                visible: sidebarContentRoot.notificationsList.length > 0
                implicitWidth: 28
                implicitHeight: 28
                icon: "clear_all"
                type: IconButton.Text
                font.pointSize: Appearance.font.size.normal

                Process {
                    id: dismissAllNotificationsProcess
                    command: ["makoctl", "dismiss", "--all"]
                    onRunningChanged: {
                        if (!running)
                            notificationsPollTimer.restart();
                    }
                }

                onClicked: dismissAllNotificationsProcess.running = true
            }
        }

        Flickable {
            id: notificationsFlickable

            Layout.fillWidth: true
            implicitHeight: Math.min(notificationsColumn.implicitHeight, sidebarContentRoot.availableHeight - sidebarLayout.spacing - 40 - Appearance.padding.large * 3)

            contentHeight: notificationsColumn.implicitHeight
            clip: true
            flickableDirection: Flickable.VerticalFlick
            boundsBehavior: Flickable.StopAtBounds

            ColumnLayout {
                id: notificationsColumn

                width: notificationsFlickable.width
                spacing: Appearance.spacing.small

                Repeater {
                    model: sidebarContentRoot.notificationsList

                    SidebarNotificationItem {
                        required property var modelData

                        Layout.fillWidth: true

                        notificationId: modelData.id
                        appName: modelData.appName
                        summary: modelData.summary
                        body: modelData.body
                        urgency: modelData.urgency
                        dismissable: !sidebarContentRoot.showingHistory

                        onDismissed: notificationsPollTimer.restart()
                    }
                }
            }
        }

        StyledText {
            Layout.fillWidth: true
            Layout.topMargin: Appearance.spacing.normal
            visible: sidebarContentRoot.notificationsList.length === 0
            text: "No notifications"
            font.pointSize: Appearance.font.size.small
            color: Colours.palette.m3onSurfaceVariant
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
