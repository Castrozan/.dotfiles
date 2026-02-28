import QtQuick

Rectangle {
    id: barWrapperRoot

    required property var screenScope

    property alias barItem: barContent

    color: ThemeColors.background

    Bar {
        id: barContent
        anchors.fill: parent
        anchors.margins: 4
        screenScope: barWrapperRoot.screenScope
    }
}
