import Quickshell
import Quickshell.DBusMenu
import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: trayMenuPopoutRoot

    required property var trayMenuHandle

    spacing: 4

    QsMenuOpener {
        id: trayMenuOpener
        menu: trayMenuPopoutRoot.trayMenuHandle
    }

    Repeater {
        model: trayMenuOpener.children

        Rectangle {
            id: trayMenuEntryDelegate

            required property var modelData

            Layout.fillWidth: true
            Layout.preferredHeight: modelData.isSeparator ? 1 : 28

            radius: 6
            color: {
                if (modelData.isSeparator) return ThemeColors.dim;
                if (trayMenuEntryMouseArea.containsMouse) return ThemeColors.surfaceTranslucent;
                return "transparent";
            }

            Loader {
                anchors.fill: parent
                active: !trayMenuEntryDelegate.modelData.isSeparator

                sourceComponent: Item {
                    anchors.fill: parent

                    Row {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 8
                        anchors.right: parent.right
                        anchors.rightMargin: 8
                        spacing: 8

                        Image {
                            anchors.verticalCenter: parent.verticalCenter
                            width: 14
                            height: 14
                            source: trayMenuEntryDelegate.modelData.icon ?? ""
                            sourceSize: Qt.size(14, 14)
                            visible: (trayMenuEntryDelegate.modelData.icon ?? "") !== ""
                        }

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: trayMenuEntryDelegate.modelData.text ?? ""
                            font.pixelSize: 12
                            font.family: "JetBrainsMono Nerd Font"
                            color: trayMenuEntryDelegate.modelData.enabled ? ThemeColors.foreground : ThemeColors.dim
                            elide: Text.ElideRight
                            width: Math.min(implicitWidth, 200)
                        }
                    }

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: parent.right
                        anchors.rightMargin: 8
                        text: "›"
                        font.pixelSize: 14
                        color: ThemeColors.foreground
                        visible: trayMenuEntryDelegate.modelData.hasChildren
                    }

                    MouseArea {
                        id: trayMenuEntryMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: trayMenuEntryDelegate.modelData.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor

                        onClicked: {
                            if (trayMenuEntryDelegate.modelData.enabled && !trayMenuEntryDelegate.modelData.hasChildren) {
                                trayMenuEntryDelegate.modelData.triggered();
                            }
                        }
                    }
                }
            }
        }
    }
}
