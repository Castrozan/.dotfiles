import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: clockModuleRoot

    spacing: 0

    property string currentHours: "00"
    property string currentMinutes: "00"
    property string currentDayOfMonth: ""
    property string currentMonthAbbreviation: ""

    readonly property var monthAbbreviations: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    function updateTime(): void {
        let now = new Date();
        currentHours = now.getHours().toString().padStart(2, "0");
        currentMinutes = now.getMinutes().toString().padStart(2, "0");
        currentDayOfMonth = now.getDate().toString();
        currentMonthAbbreviation = monthAbbreviations[now.getMonth()];
    }

    Timer {
        interval: 10000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: clockModuleRoot.updateTime()
    }

    Text {
        Layout.alignment: Qt.AlignHCenter
        text: clockModuleRoot.currentHours
        font.pixelSize: 16
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    Text {
        Layout.alignment: Qt.AlignHCenter
        text: clockModuleRoot.currentMinutes
        font.pixelSize: 16
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    Rectangle {
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 4
        Layout.bottomMargin: 4
        width: 20
        height: 1
        color: ThemeColors.dim
    }

    Text {
        Layout.alignment: Qt.AlignHCenter
        text: clockModuleRoot.currentDayOfMonth
        font.pixelSize: 14
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    Text {
        Layout.alignment: Qt.AlignHCenter
        text: clockModuleRoot.currentMonthAbbreviation
        font.pixelSize: 11
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.dim
    }
}
