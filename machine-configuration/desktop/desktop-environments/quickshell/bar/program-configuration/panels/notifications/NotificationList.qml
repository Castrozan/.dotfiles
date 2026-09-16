pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import ".."
import "../../dashboard"

Flickable {
    id: notificationsFlickable

    required property real availableHeight
    required property var notifications
    required property int focusedIndex
    required property int expandedIndex

    signal dismissRequested(int index)
    signal notificationClicked(int index)

    function ensureVisible(notificationIndex: int): void {
        let item = notificationItemsRepeater.itemAt(notificationIndex);
        if (!item)
            return;
        let itemTop = item.y;
        let itemBottom = item.y + item.height;
        if (itemTop < notificationsFlickable.contentY)
            notificationsFlickable.contentY = itemTop;
        else if (itemBottom > notificationsFlickable.contentY + notificationsFlickable.height)
            notificationsFlickable.contentY = itemBottom - notificationsFlickable.height;
    }

    implicitHeight: Math.min(notificationsColumn.implicitHeight, notificationsFlickable.availableHeight)

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
            model: notificationsFlickable.notifications

            SidebarNotificationItem {
                required property var modelData
                required property int index

                Layout.fillWidth: true

                notificationId: modelData.id
                appName: modelData.appName
                summary: modelData.summary
                body: modelData.body
                urgency: modelData.urgency
                dismissable: true
                focused: index === notificationsFlickable.focusedIndex
                expanded: index === notificationsFlickable.expandedIndex

                onDismissRequested: {
                    notificationsFlickable.dismissRequested(index);
                }
                onClicked: {
                    notificationsFlickable.notificationClicked(index);
                }
            }
        }
    }
}
