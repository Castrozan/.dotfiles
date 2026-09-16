import QtQuick

Item {
    id: barWrapperRoot

    required property var screenScope

    property alias barItem: barContent

    Bar {
        id: barContent
        anchors.fill: parent
        anchors.margins: 4
        screenScope: barWrapperRoot.screenScope
    }
}
