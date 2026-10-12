import QtQuick

Item {
    id: barWrapperRoot

    required property var screenScope
    required property bool barVisible

    property alias barItem: barContent

    signal hoverChanged(bool hovered)

    x: barVisible ? 0 : -width
    visible: x > -width

    Behavior on x {
        NumberAnimation {
            duration: 350
            easing.type: Easing.OutCubic
        }
    }

    HoverHandler {
        onHoveredChanged: barWrapperRoot.hoverChanged(hovered)
    }

    Bar {
        id: barContent
        anchors.fill: parent
        anchors.margins: 4
        screenScope: barWrapperRoot.screenScope
    }
}
