import QtQuick
import ".."

Rectangle {
    id: statusIconsTriggerButtonRoot

    required property var barRoot
    required property var screenScope

    readonly property bool isHovered: statusIconsTriggerButtonMouseArea.containsMouse

    radius: 6
    color: statusIconsTriggerButtonMouseArea.containsMouse ? ThemeColors.surfaceTranslucent : "transparent"

    Component.onCompleted: _registerTriggerPosition()
    onYChanged: _registerTriggerPosition()
    onHeightChanged: _registerTriggerPosition()

    function _registerTriggerPosition(): void {
        if (!barRoot) return;
        let globalPos = mapToItem(barRoot, 0, 0);
        barRoot.registerStatusIconPosition("statusicons", globalPos.y, globalPos.y + height);
    }

    Column {
        anchors.centerIn: parent
        spacing: 2

        Repeater {
            model: 3

            Rectangle {
                width: 3
                height: 3
                radius: 1.5
                color: ThemeColors.foreground
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }

    MouseArea {
        id: statusIconsTriggerButtonMouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onContainsMouseChanged: {
            if (containsMouse && statusIconsTriggerButtonRoot.screenScope) {
                let scenePos = statusIconsTriggerButtonRoot.mapToItem(null, 0, statusIconsTriggerButtonRoot.height / 2);
                statusIconsTriggerButtonRoot.screenScope.showPopout("statusicons", scenePos.y);
            }
        }
    }
}
