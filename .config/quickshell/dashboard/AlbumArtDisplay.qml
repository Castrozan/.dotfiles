import QtQuick

Rectangle {
    id: albumArtDisplayRoot

    property string artUrl: ""

    width: 150
    height: 150
    radius: 12
    color: ThemeColors.surfaceTranslucent
    clip: true

    Image {
        id: albumArtImage
        anchors.fill: parent
        source: albumArtDisplayRoot.artUrl
        fillMode: Image.PreserveAspectCrop
        visible: status === Image.Ready
        smooth: true
    }

    Text {
        anchors.centerIn: parent
        text: "󰎈"
        font.pixelSize: 48
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.dim
        visible: albumArtImage.status !== Image.Ready
    }
}
