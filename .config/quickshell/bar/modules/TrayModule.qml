import Quickshell.Services.SystemTray
import Qt5Compat.GraphicalEffects
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
                id: trayItemIcon
                anchors.centerIn: parent
                width: 16
                height: 16
                source: trayItemDelegate.modelData.icon ?? ""
                sourceSize: Qt.size(16, 16)
                smooth: true
            }

            Colorize {
                anchors.fill: trayItemIcon
                source: trayItemIcon
                hue: ThemeColors.foreground.hslHue
                saturation: ThemeColors.foreground.hslSaturation
                lightness: 0.3
            }

            MouseArea {
                id: trayItemMouseArea
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                cursorShape: Qt.PointingHandCursor

                onClicked: mouse => {
                    let popoutName = "traymenu" + trayItemDelegate.index;
                    if (trayModuleRoot.screenScope.popoutCurrentName === popoutName) {
                        trayModuleRoot.screenScope.popoutCurrentName = "";
                        return;
                    }
                    if (mouse.button === Qt.LeftButton && !trayItemDelegate.modelData.onlyMenu) {
                        trayItemDelegate.modelData.activate();
                    }
                    let scenePos = trayItemDelegate.mapToItem(null, 0, trayItemDelegate.height / 2);
                    trayModuleRoot.screenScope.showPopout(popoutName, scenePos.y);
                }
            }
        }
    }
}
