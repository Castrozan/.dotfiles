pragma ComponentBehavior: Bound

import "../dashboard/components"
import "../dashboard"
import "notifications"
import QtQuick
import QtQuick.Layouts

FocusScope {
    id: sidebarContentRoot

    property real availableHeight: 400
    property bool sidebarActive: false
    property var hiddenHistoryNotificationIds: ({})
    property var filteredHistoryNotificationsList: notificationFeed.historyNotificationsList.filter(n => !hiddenHistoryNotificationIds[n.id])
    property var notificationsList: notificationFeed.activeNotificationsList.length > 0 ? notificationFeed.activeNotificationsList : filteredHistoryNotificationsList
    property bool showingHistory: notificationFeed.activeNotificationsList.length === 0 && filteredHistoryNotificationsList.length > 0
    property int currentFocusedNotificationIndex: -1
    property int expandedNotificationIndex: -1

    NotificationFeed {
        id: notificationFeed
    }

    signal closeRequested

    implicitWidth: 300
    implicitHeight: Math.min(sidebarLayout.implicitHeight + Appearance.padding.large * 2, availableHeight)

    onSidebarActiveChanged: {
        if (sidebarActive) {
            currentFocusedNotificationIndex = notificationsList.length > 0 ? 0 : -1;
            expandedNotificationIndex = -1;
            focusActivationTimer.restart();
        }
    }

    Timer {
        id: focusActivationTimer
        interval: 50
        onTriggered: sidebarContentRoot.forceActiveFocus()
    }

    onNotificationsListChanged: {
        if (currentFocusedNotificationIndex >= notificationsList.length)
            currentFocusedNotificationIndex = notificationsList.length - 1;
        if (expandedNotificationIndex >= notificationsList.length)
            expandedNotificationIndex = -1;
    }

    function moveFocusUp(): void {
        if (notificationsList.length === 0)
            return;
        if (currentFocusedNotificationIndex <= 0)
            currentFocusedNotificationIndex = notificationsList.length - 1;
        else
            currentFocusedNotificationIndex--;
        notificationList.ensureVisible(currentFocusedNotificationIndex);
    }

    function moveFocusDown(): void {
        if (notificationsList.length === 0)
            return;
        if (currentFocusedNotificationIndex >= notificationsList.length - 1)
            currentFocusedNotificationIndex = 0;
        else
            currentFocusedNotificationIndex++;
        notificationList.ensureVisible(currentFocusedNotificationIndex);
    }

    function toggleExpandFocusedNotification(): void {
        if (currentFocusedNotificationIndex < 0 || currentFocusedNotificationIndex >= notificationsList.length)
            return;
        expandedNotificationIndex = expandedNotificationIndex === currentFocusedNotificationIndex ? -1 : currentFocusedNotificationIndex;
    }

    function dismissNotificationAtIndex(indexToDismiss: int): void {
        if (indexToDismiss < 0 || indexToDismiss >= notificationsList.length)
            return;
        let notif = notificationsList[indexToDismiss];
        if (showingHistory) {
            let updated = Object.assign({}, hiddenHistoryNotificationIds);
            updated[notif.id] = true;
            hiddenHistoryNotificationIds = updated;
        } else {
            notificationFeed.dismissNotification(notif.id);
        }
    }

    function dismissFocusedNotification(): void {
        dismissNotificationAtIndex(currentFocusedNotificationIndex);
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

    ColumnLayout {
        id: sidebarLayout

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: Appearance.padding.large

        spacing: Appearance.spacing.small

        NotificationHeader {
            showingHistory: sidebarContentRoot.showingHistory
            notificationCount: sidebarContentRoot.notificationsList.length
            onClearRequested: notificationFeed.dismissAll()
        }

        NotificationList {
            id: notificationList

            Layout.fillWidth: true
            availableHeight: sidebarContentRoot.availableHeight - sidebarLayout.spacing - 40 - Appearance.padding.large * 3
            notifications: sidebarContentRoot.notificationsList
            focusedIndex: sidebarContentRoot.currentFocusedNotificationIndex
            expandedIndex: sidebarContentRoot.expandedNotificationIndex
            onDismissRequested: index => sidebarContentRoot.dismissNotificationAtIndex(index)
            onNotificationClicked: index => {
                sidebarContentRoot.currentFocusedNotificationIndex = index;
                sidebarContentRoot.expandedNotificationIndex = sidebarContentRoot.expandedNotificationIndex === index ? -1 : index;
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
