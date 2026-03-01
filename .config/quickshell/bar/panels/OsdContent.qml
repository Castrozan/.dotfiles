pragma ComponentBehavior: Bound

import Quickshell.Io
import "../dashboard/components"
import "../dashboard"
import QtQuick
import QtQuick.Layouts

Item {
    id: osdContentRoot

    property string osdType: "volume"
    property int osdValue: 0
    property bool osdMuted: false

    signal interactionKeepAlive()

    implicitWidth: 56
    implicitHeight: osdSliderColumn.implicitHeight + Appearance.padding.large * 2

    function applyValueFromMouseY(mouseY: real, trackHeight: real): void {
        let fraction = 1.0 - Math.max(0, Math.min(mouseY, trackHeight)) / trackHeight;
        let newValue = Math.round(fraction * 100);
        osdContentRoot.osdValue = newValue;
        osdContentRoot.interactionKeepAlive();

        if (osdContentRoot.osdType === "brightness")
            setValueProcess.command = ["brightnessctl", "set", newValue + "%"];
        else if (osdContentRoot.osdType === "mic")
            setValueProcess.command = ["pactl", "set-source-volume", "@DEFAULT_SOURCE@", newValue + "%"];
        else
            setValueProcess.command = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", newValue + "%"];

        setValueProcess.running = true;
    }

    Process {
        id: setValueProcess
    }

    ColumnLayout {
        id: osdSliderColumn

        anchors.centerIn: parent
        spacing: Appearance.spacing.small

        MaterialIcon {
            Layout.alignment: Qt.AlignHCenter
            text: {
                if (osdContentRoot.osdType === "brightness") return "brightness_6";
                if (osdContentRoot.osdType === "mic") return osdContentRoot.osdMuted ? "mic_off" : "mic";
                return osdContentRoot.osdMuted ? "volume_off" : "volume_up";
            }
            color: osdContentRoot.osdMuted ? Colours.palette.m3error : Colours.palette.m3primary
            font.pointSize: Appearance.font.size.extraLarge
        }

        Item {
            id: sliderTrack

            Layout.alignment: Qt.AlignHCenter
            implicitWidth: 32
            implicitHeight: 120

            StyledRect {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: 24
                color: Colours.palette.m3surfaceContainerHighest
                radius: Appearance.rounding.full
            }

            StyledRect {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                width: 24

                readonly property real clampedFraction: Math.min(osdContentRoot.osdValue / 100.0, 1.0)

                height: parent.height * (osdContentRoot.osdMuted ? 0 : clampedFraction)
                color: osdContentRoot.osdMuted ? Colours.palette.m3error : osdContentRoot.osdValue > 100 ? Colours.palette.m3error : Colours.palette.m3primary
                radius: Appearance.rounding.full

                Behavior on height {
                    NumberAnimation {
                        duration: 100
                        easing.type: Easing.OutCubic
                    }
                }
            }

            MouseArea {
                anchors.fill: parent
                hoverEnabled: true

                onPressed: event => {
                    osdContentRoot.applyValueFromMouseY(event.y, sliderTrack.height);
                }

                onPositionChanged: event => {
                    if (pressed)
                        osdContentRoot.applyValueFromMouseY(event.y, sliderTrack.height);
                }

                onWheel: event => {
                    let delta = event.angleDelta.y > 0 ? 5 : -5;
                    let newValue = Math.max(0, Math.min(100, osdContentRoot.osdValue + delta));
                    osdContentRoot.osdValue = newValue;
                    osdContentRoot.interactionKeepAlive();

                    if (osdContentRoot.osdType === "brightness")
                        setValueProcess.command = ["brightnessctl", "set", newValue + "%"];
                    else if (osdContentRoot.osdType === "mic")
                        setValueProcess.command = ["pactl", "set-source-volume", "@DEFAULT_SOURCE@", newValue + "%"];
                    else
                        setValueProcess.command = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", newValue + "%"];

                    setValueProcess.running = true;
                }
            }
        }

        StyledText {
            Layout.alignment: Qt.AlignHCenter
            text: osdContentRoot.osdMuted ? "M" : osdContentRoot.osdValue + "%"
            font.pointSize: Appearance.font.size.small
            color: Colours.palette.m3onSurfaceVariant
        }
    }
}
