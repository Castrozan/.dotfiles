pragma ComponentBehavior: Bound

import "../components"
import "media"
import "../services"
import "../widgets"
import ".."
import Quickshell.Services.Mpris
import QtQuick
import QtQuick.Layouts

Item {
    id: mediaTabRoot

    property bool dashboardIsActive: false

    property real playerProgress: {
        const activePlayer = PlayersService.active;
        return activePlayer?.length ? activePlayer.position / activePlayer.length : 0;
    }

    readonly property bool isCurrentlyPlaying: PlayersService.active?.isPlaying ?? false

    implicitWidth: cavaVisualiserContainer.implicitWidth + Appearance.spacing.normal + detailsColumn.implicitWidth + Appearance.spacing.normal + bongoCatContainer.implicitWidth
    implicitHeight: 320

    Behavior on playerProgress {
        Anim {
            duration: Appearance.anim.durations.large
        }
    }

    Timer {
        running: mediaTabRoot.isCurrentlyPlaying && mediaTabRoot.dashboardIsActive
        interval: DashboardConfig.mediaUpdateInterval
        triggeredOnStart: true
        repeat: true
        onTriggered: PlayersService.active?.positionChanged()
    }

    Item {
        id: cavaVisualiserContainer

        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter

        implicitWidth: 180
        implicitHeight: 280

        Component.onDestruction: {
            if (mediaTabRoot.dashboardIsActive)
                CavaService.refCount--;
        }

        Connections {
            target: mediaTabRoot
            function onDashboardIsActiveChanged() {
                if (mediaTabRoot.dashboardIsActive)
                    CavaService.refCount++;
                else
                    CavaService.refCount--;
            }
        }

        Row {
            anchors.bottom: parent.bottom
            anchors.bottomMargin: parent.height * 0.1
            anchors.horizontalCenter: parent.horizontalCenter

            height: parent.height * 0.8
            spacing: 2

            Repeater {
                model: CavaService.barCount

                Rectangle {
                    id: cavaBar

                    required property int index

                    readonly property real barValue: {
                        const currentValues = CavaService.values;
                        return (currentValues && index < currentValues.length) ? currentValues[index] : 0;
                    }

                    width: (cavaVisualiserContainer.implicitWidth - (CavaService.barCount - 1) * 2) / CavaService.barCount
                    height: Math.max(2, barValue * parent.height)
                    anchors.bottom: parent.bottom
                    radius: width / 2
                    color: Colours.palette.m3primary
                    opacity: 0.5 + barValue * 0.5

                    Behavior on height {
                        Anim {
                            duration: Appearance.anim.durations.small
                        }
                    }

                    Behavior on opacity {
                        Anim {
                            duration: Appearance.anim.durations.small
                        }
                    }

                    Behavior on color {
                        CAnim {}
                    }
                }
            }
        }
    }

    MediaPlaybackDetails {
        id: detailsColumn
        playerProgress: mediaTabRoot.playerProgress
        anchors.left: cavaVisualiserContainer.right
        anchors.leftMargin: Appearance.spacing.normal
        anchors.verticalCenter: parent.verticalCenter
    }

    Item {
        id: bongoCatContainer

        anchors.left: detailsColumn.right
        anchors.leftMargin: Appearance.spacing.normal
        anchors.verticalCenter: parent.verticalCenter

        implicitWidth: cavaVisualiserContainer.implicitWidth
        implicitHeight: cavaVisualiserContainer.implicitHeight

        AnimatedImage {
            anchors.centerIn: parent

            width: parent.width * 0.75
            height: parent.height * 0.75

            playing: mediaTabRoot.isCurrentlyPlaying
            speed: DashboardConfig.bongoCatGifSpeed
            source: Qt.resolvedUrl("../../assets/bongocat.gif")
            asynchronous: true
            fillMode: AnimatedImage.PreserveAspectFit
        }
    }
}
