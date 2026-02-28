import Quickshell.Services.Mpris
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: mediaDashboardPanelRoot

    property MprisPlayer activePlayer: null

    width: 480
    implicitHeight: panelContentLayout.implicitHeight + 32
    radius: 16
    color: ThemeColors.backgroundTranslucent

    RowLayout {
        id: panelContentLayout
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        AlbumArtDisplay {
            artUrl: mediaDashboardPanelRoot.activePlayer ? mediaDashboardPanelRoot.activePlayer.trackArtUrl : ""
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12

            TrackInformationDisplay {
                Layout.fillWidth: true
                trackTitle: mediaDashboardPanelRoot.activePlayer ? mediaDashboardPanelRoot.activePlayer.trackTitle : ""
                trackAlbum: mediaDashboardPanelRoot.activePlayer ? mediaDashboardPanelRoot.activePlayer.trackAlbum : ""
                trackArtist: mediaDashboardPanelRoot.activePlayer ? mediaDashboardPanelRoot.activePlayer.trackArtist : ""
            }

            SeekProgressBar {
                Layout.fillWidth: true
                activePlayer: mediaDashboardPanelRoot.activePlayer
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                PlaybackControlsRow {
                    activePlayer: mediaDashboardPanelRoot.activePlayer
                }

                Item { Layout.fillWidth: true }

                PlayerSourceIndicator {
                    activePlayer: mediaDashboardPanelRoot.activePlayer
                }
            }
        }
    }
}
