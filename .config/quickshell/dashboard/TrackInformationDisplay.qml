import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: trackInformationDisplayRoot

    property string trackTitle: ""
    property string trackAlbum: ""
    property string trackArtist: ""

    spacing: 4

    Text {
        Layout.fillWidth: true
        text: trackInformationDisplayRoot.trackTitle || "No Track"
        font.pixelSize: 18
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
        elide: Text.ElideRight
        maximumLineCount: 1
    }

    Text {
        Layout.fillWidth: true
        text: trackInformationDisplayRoot.trackAlbum
        font.pixelSize: 12
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.dim
        elide: Text.ElideRight
        maximumLineCount: 1
        visible: text !== ""
    }

    Text {
        Layout.fillWidth: true
        text: trackInformationDisplayRoot.trackArtist
        font.pixelSize: 14
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.accent
        elide: Text.ElideRight
        maximumLineCount: 1
        visible: text !== ""
    }
}
