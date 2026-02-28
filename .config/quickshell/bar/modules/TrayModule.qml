import Quickshell.Services.SystemTray
import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: trayModuleRoot

    required property var screenScope

    spacing: 2

    Repeater {
        model: SystemTray.items

        Rectangle {
            id: trayItemDelegate

            required property SystemTrayItem modelData
            required property int index

            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 28
            Layout.preferredHeight: 28

            radius: 6
            color: trayItemMouseArea.containsMouse ? ThemeColors.surfaceTranslucent : "transparent"

            Image {
                anchors.centerIn: parent
                width: 16
                height: 16
                source: trayItemDelegate.modelData.icon ?? ""
                sourceSize: Qt.size(16, 16)
                smooth: true
            }

            MouseArea {
                id: trayItemMouseArea
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                cursorShape: Qt.PointingHandCursor

                onClicked: mouse => {
                    if (mouse.button === Qt.RightButton || trayItemDelegate.modelData.onlyMenu) {
                        _showTrayMenuPopout();
                    } else {
                        trayItemDelegate.modelData.activate();
                    }
                }

                function _showTrayMenuPopout(): void {
                    let scenePos = trayItemDelegate.mapToItem(null, 0, trayItemDelegate.height / 2);
                    trayModuleRoot.screenScope.showPopout("traymenu" + trayItemDelegate.index, scenePos.y);
                }
            }
        }
    }
}
