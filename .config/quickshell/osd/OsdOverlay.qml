import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import QtQuick.Layouts

Scope {
    id: osdRoot

    property string osdType: "volume"
    property int osdValue: 0
    property bool osdMuted: false
    property bool osdVisible: false

    readonly property string themeColorsPath: `${Quickshell.env("HOME")}/.config/hypr-theme/current/theme/quickshell-osd-colors.json`

    readonly property string volumeIcon: "\u{1F50A}"
    readonly property string volumeMutedIcon: "\u{1F507}"
    readonly property string brightnessIcon: "\u{2600}"
    readonly property string microphoneIcon: "\u{1F3A4}"
    readonly property string microphoneMutedIcon: "\u{1F399}"

    function parseThemeColors(jsonText: string): var {
        try {
            return JSON.parse(jsonText);
        } catch (error) {
            return null;
        }
    }

    function rgbStringToQtColor(rgbString: string, alpha: real): color {
        let parts = rgbString.split(",");
        if (parts.length !== 3) return Qt.rgba(0, 0, 0, alpha);
        return Qt.rgba(
            parseInt(parts[0].trim()) / 255.0,
            parseInt(parts[1].trim()) / 255.0,
            parseInt(parts[2].trim()) / 255.0,
            alpha
        );
    }

    readonly property var themeColors: themeColorsFile.loaded ? parseThemeColors(themeColorsFile.text()) : null

    readonly property color themeBackground: themeColors ? rgbStringToQtColor(themeColors.backgroundRgb, 0.85) : Qt.rgba(0, 0, 0, 0.75)
    readonly property color themeForeground: themeColors ? themeColors.foreground : "white"
    readonly property color themeAccent: themeColors ? themeColors.accent : "white"
    readonly property color themeError: themeColors ? themeColors.error : Qt.rgba(1, 0.3, 0.3, 0.9)
    readonly property color themeBarTrack: themeColors ? rgbStringToQtColor(themeColors.foregroundRgb, 0.2) : Qt.rgba(1, 1, 1, 0.2)
    readonly property color themeMutedBar: themeColors ? rgbStringToQtColor(themeColors.errorRgb, 0.8) : Qt.rgba(1, 0.3, 0.3, 0.8)

    function iconForCurrentState(): string {
        if (osdType === "volume") return osdMuted ? volumeMutedIcon : volumeIcon;
        if (osdType === "brightness") return brightnessIcon;
        if (osdType === "mic") return osdMuted ? microphoneMutedIcon : microphoneIcon;
        return volumeIcon;
    }

    function handleOsdMessage(message: string): void {
        try {
            let parsed = JSON.parse(message);
            osdType = parsed.type ?? "volume";
            osdValue = parsed.value ?? 0;
            osdMuted = parsed.muted ?? false;
            osdVisible = true;
            hideTimer.restart();
        } catch (error) {
            console.warn("quickshell-osd: failed to parse message:", message);
        }
    }

    FileView {
        id: themeColorsFile
        path: Qt.url(`file://${themeColorsPath}`)
        watchChanges: true
        blockLoading: true
        onFileChanged: this.reload()
    }

    SocketServer {
        active: true
        path: "/tmp/quickshell-osd.sock"

        handler: Socket {
            parser: SplitParser {
                splitMarker: "\n"
                onRead: message => osdRoot.handleOsdMessage(message)
            }
        }
    }

    Timer {
        id: hideTimer
        interval: 1500
        repeat: false
        onTriggered: osdVisible = false
    }

    PanelWindow {
        id: osdPanel

        anchors {
            bottom: true
        }

        margins.bottom: 100

        implicitHeight: 60
        implicitWidth: 300

        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "quickshell-osd"

        color: "transparent"
        surfaceFormat.opaque: false

        visible: osdVisible

        Rectangle {
            anchors.centerIn: parent
            width: 300
            height: 50
            radius: 25
            color: themeBackground

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 12

                Text {
                    text: iconForCurrentState()
                    font.pixelSize: 20
                    color: themeForeground
                    Layout.alignment: Qt.AlignVCenter
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 6
                    Layout.alignment: Qt.AlignVCenter
                    radius: 3
                    color: themeBarTrack

                    Rectangle {
                        readonly property real clampedFraction: Math.min(osdValue / 100.0, 1.0)
                        readonly property bool isOverdriven: osdValue > 100

                        width: parent.width * (osdMuted ? 0 : clampedFraction)
                        height: parent.height
                        radius: 3
                        color: osdMuted ? themeMutedBar : isOverdriven ? themeError : themeAccent

                        Behavior on width {
                            NumberAnimation {
                                duration: 100
                                easing.type: Easing.OutCubic
                            }
                        }

                        Behavior on color {
                            ColorAnimation {
                                duration: 150
                            }
                        }
                    }
                }

                Text {
                    text: osdMuted ? "Muted" : osdValue + "%"
                    font.pixelSize: 14
                    font.bold: true
                    color: themeForeground
                    horizontalAlignment: Text.AlignRight
                    Layout.preferredWidth: 48
                    Layout.alignment: Qt.AlignVCenter
                }
            }
        }
    }
}
