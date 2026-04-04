import Quickshell
import Quickshell.DBusMenu
import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: trayMenuPopoutRoot

    required property var trayMenuHandle

    spacing: 2

    QsMenuOpener {
        id: trayMenuOpener
        menu: trayMenuPopoutRoot.trayMenuHandle
    }

    Repeater {
        model: trayMenuOpener.children

        Rectangle {
            id: trayMenuEntryDelegate

            required property var modelData

            readonly property bool itemEnabled: modelData.enabled !== false

            Layout.fillWidth: true
            Layout.preferredHeight: modelData.isSeparator ? 9 : 30
            Layout.leftMargin: modelData.isSeparator ? 8 : 0
            Layout.rightMargin: modelData.isSeparator ? 8 : 0

            radius: modelData.isSeparator ? 0 : 6
            color: {
                if (modelData.isSeparator) return "transparent";
                if (trayMenuEntryMouseArea.containsMouse) return ThemeColors.surfaceTranslucent;
                return "transparent";
            }

            Rectangle {
                visible: trayMenuEntryDelegate.modelData.isSeparator
                anchors.centerIn: parent
                width: parent.width
                height: 1
                color: Qt.rgba(ThemeColors.foreground.r, ThemeColors.foreground.g, ThemeColors.foreground.b, 0.15)
            }

            Loader {
                anchors.fill: parent
                active: !trayMenuEntryDelegate.modelData.isSeparator

                sourceComponent: Item {
                    anchors.fill: parent

                    Row {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 10
                        anchors.right: parent.right
                        anchors.rightMargin: 10
                        spacing: 8

                        Image {
                            anchors.verticalCenter: parent.verticalCenter
                            width: 16
                            height: 16
                            source: trayMenuEntryDelegate.modelData.icon ?? ""
                            sourceSize: Qt.size(16, 16)
                            visible: (trayMenuEntryDelegate.modelData.icon ?? "") !== ""
                        }

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: trayMenuEntryDelegate.modelData.text ?? ""
                            font.pixelSize: 13
                            font.family: "JetBrainsMono Nerd Font"
                            color: trayMenuEntryDelegate.itemEnabled
                                ? ThemeColors.foreground
                                : Qt.rgba(ThemeColors.foreground.r, ThemeColors.foreground.g, ThemeColors.foreground.b, 0.4)
                            elide: Text.ElideRight
                            width: Math.min(implicitWidth, 220)
                        }
                    }

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: parent.right
                        anchors.rightMargin: 10
                        text: "›"
                        font.pixelSize: 14
                        color: ThemeColors.foreground
                        visible: trayMenuEntryDelegate.modelData.hasChildren
                    }

                    MouseArea {
                        id: trayMenuEntryMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: trayMenuEntryDelegate.itemEnabled ? Qt.PointingHandCursor : Qt.ArrowCursor

                        onClicked: {
                            if (trayMenuEntryDelegate.itemEnabled && !trayMenuEntryDelegate.modelData.hasChildren) {
                                trayMenuEntryDelegate.modelData.triggered();
                            }
                        }
                    }
                }
            }
        }
    }
}
