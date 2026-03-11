pragma ComponentBehavior: Bound

import Quickshell.Io
import "../dashboard/components"
import "../dashboard"
import QtQuick
import QtQuick.Layouts

FocusScope {
    id: sidebarContentRoot

    property real availableHeight: 400
    property bool sidebarActive: false
    property var activeNotificationsList: []
    property var historyNotificationsList: []
    property var notificationsList: activeNotificationsList.length > 0 ? activeNotificationsList : historyNotificationsList
    property bool showingHistory: activeNotificationsList.length === 0 && historyNotificationsList.length > 0
    property int currentFocusedNotificationIndex: -1
    property int expandedNotificationIndex: -1

    signal closeRequested()

    implicitWidth: 300
    implicitHeight: Math.min(sidebarLayout.implicitHeight + Appearance.padding.large * 2, availableHeight)

    onSidebarActiveChanged: {
        if (sidebarActive) {
            currentFocusedNotificationIndex = notificationsList.length > 0 ? 0 : -1;
            expandedNotificationIndex = -1;
            forceActiveFocus();
        }
    }

    onNotificationsListChanged: {
        if (currentFocusedNotificationIndex >= notificationsList.length)
            currentFocusedNotificationIndex = notificationsList.length - 1;
        if (expandedNotificationIndex >= notificationsList.length)
            expandedNotificationIndex = -1;
    }

    function moveFocusUp(): void {
        if (notificationsList.length === 0) return;
        if (currentFocusedNotificationIndex <= 0)
            currentFocusedNotificationIndex = notificationsList.length - 1;
        else
            currentFocusedNotificationIndex--;
        ensureFocusedItemVisible();
    }

    function moveFocusDown(): void {
        if (notificationsList.length === 0) return;
        if (currentFocusedNotificationIndex >= notificationsList.length - 1)
            currentFocusedNotificationIndex = 0;
        else
            currentFocusedNotificationIndex++;
        ensureFocusedItemVisible();
    }

    function toggleExpandFocusedNotification(): void {
        if (currentFocusedNotificationIndex < 0 || currentFocusedNotificationIndex >= notificationsList.length) return;
        expandedNotificationIndex = expandedNotificationIndex === currentFocusedNotificationIndex ? -1 : currentFocusedNotificationIndex;
    }

    function dismissFocusedNotification(): void {
        if (currentFocusedNotificationIndex < 0 || currentFocusedNotificationIndex >= notificationsList.length) return;
        if (showingHistory) return;
        let notif = notificationsList[currentFocusedNotificationIndex];
        keyboardDismissProcess.command = ["makoctl", "dismiss", "-n", String(notif.id)];
        keyboardDismissProcess.running = true;
    }

    function ensureFocusedItemVisible(): void {
        let item = notificationItemsRepeater.itemAt(currentFocusedNotificationIndex);
        if (!item) return;
        let itemTop = item.y;
        let itemBottom = item.y + item.height;
        if (itemTop < notificationsFlickable.contentY)
            notificationsFlickable.contentY = itemTop;
        else if (itemBottom > notificationsFlickable.contentY + notificationsFlickable.height)
            notificationsFlickable.contentY = itemBottom - notificationsFlickable.height;
    }

    Keys.onPressed: event => {
        if (event.key === Qt.Key_K || event.key === Qt.Key_Up) {
            sidebarContentRoot.moveFocusUp();
            event.accepted = true;
        } else if (event.key === Qt.Key_J || event.key === Qt.Key_Down) {
            sidebarContentRoot.moveFocusDown();
            event.accepted = true;
        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            sidebarContentRoot.toggleExpandFocusedNotification();
            event.accepted = true;
        } else if (event.key === Qt.Key_Delete || event.key === Qt.Key_D) {
            sidebarContentRoot.dismissFocusedNotification();
            event.accepted = true;
        } else if (event.key === Qt.Key_Escape) {
            if (sidebarContentRoot.expandedNotificationIndex >= 0) {
                sidebarContentRoot.expandedNotificationIndex = -1;
            } else {
                sidebarContentRoot.closeRequested();
            }
            event.accepted = true;
        }
    }

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

    Process {
        id: keyboardDismissProcess
        onRunningChanged: {
            if (!running)
                notificationsPollTimer.restart();
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
                    id: notificationItemsRepeater
                    model: sidebarContentRoot.notificationsList

                    SidebarNotificationItem {
                        required property var modelData
                        required property int index

                        Layout.fillWidth: true

                        notificationId: modelData.id
                        appName: modelData.appName
                        summary: modelData.summary
                        body: modelData.body
                        urgency: modelData.urgency
                        dismissable: !sidebarContentRoot.showingHistory
                        focused: index === sidebarContentRoot.currentFocusedNotificationIndex
                        expanded: index === sidebarContentRoot.expandedNotificationIndex

                        onDismissed: notificationsPollTimer.restart()
                        onClicked: {
                            sidebarContentRoot.currentFocusedNotificationIndex = index;
                            sidebarContentRoot.expandedNotificationIndex = sidebarContentRoot.expandedNotificationIndex === index ? -1 : index;
                        }
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
