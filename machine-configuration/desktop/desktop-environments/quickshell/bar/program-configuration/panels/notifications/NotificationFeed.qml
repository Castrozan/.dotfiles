import Quickshell
import Quickshell.Io
import QtQuick

Scope {
    id: notificationFeedRoot

    property var activeNotificationsList: []
    property var historyNotificationsList: []

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
                notificationFeedRoot.activeNotificationsList = notificationFeedRoot.extractNotificationsFromBusctlJson(data);
            }
        }
    }

    Process {
        id: historyNotificationsQueryProcess
        command: ["busctl", "--user", "--json=short", "call", "org.freedesktop.Notifications", "/fr/emersion/Mako", "fr.emersion.Mako", "ListHistory"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                notificationFeedRoot.historyNotificationsList = notificationFeedRoot.extractNotificationsFromBusctlJson(data);
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

    Process {
        id: dismissAllNotificationsProcess
        command: ["makoctl", "dismiss", "--all"]
        onRunningChanged: {
            if (!running)
                notificationsPollTimer.restart();
        }
    }

    function dismissNotification(notificationId: int): void {
        keyboardDismissProcess.command = ["makoctl", "dismiss", "-n", String(notificationId)];
        keyboardDismissProcess.running = true;
    }

    function dismissAll(): void {
        dismissAllNotificationsProcess.running = true;
    }
}
