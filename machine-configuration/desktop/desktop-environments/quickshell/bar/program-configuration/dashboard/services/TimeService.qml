pragma Singleton

import ".."
import Quickshell
import QtQuick

Singleton {
    property alias enabled: systemClock.enabled
    readonly property date date: systemClock.date
    readonly property int hours: systemClock.hours
    readonly property int minutes: systemClock.minutes
    readonly property int seconds: systemClock.seconds

    readonly property string timeStr: formatDateTime(DashboardConfig.useTwelveHourClock ? "hh:mm:A" : "hh:mm")
    readonly property list<string> timeComponents: timeStr.split(":")
    readonly property string hourStr: timeComponents[0] ?? ""
    readonly property string minuteStr: timeComponents[1] ?? ""
    readonly property string amPmStr: timeComponents[2] ?? ""

    function formatDateTime(formatString: string): string {
        return Qt.formatDateTime(systemClock.date, formatString);
    }

    SystemClock {
        id: systemClock
        precision: SystemClock.Seconds
    }
}
