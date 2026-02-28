import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: clockModuleRoot

    spacing: 0

    property string currentHours: "00"
    property string currentMinutes: "00"

    function updateTime(): void {
        let now = new Date();
        currentHours = now.getHours().toString().padStart(2, "0");
        currentMinutes = now.getMinutes().toString().padStart(2, "0");
    }

    Timer {
        interval: 1000
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
}
