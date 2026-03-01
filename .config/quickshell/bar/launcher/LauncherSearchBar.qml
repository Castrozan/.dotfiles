pragma ComponentBehavior: Bound

import "../dashboard/components"
import "../dashboard"
import ".."
import "."
import QtQuick

StyledRect {
    id: launcherSearchBarRoot

    property alias searchText: searchTextInput.text
    property bool launcherVisible: false

    signal accepted

    function focusInput(): void {
        searchTextInput.forceActiveFocus();
    }

    function clearSearch(): void {
        searchTextInput.text = "";
    }

    implicitHeight: LauncherConfig.searchBarHeight
    radius: Appearance.rounding.full
    color: Colours.palette.m3surfaceContainer

    MaterialIcon {
        id: searchIcon

        anchors.left: parent.left
        anchors.leftMargin: Appearance.padding.large
        anchors.verticalCenter: parent.verticalCenter

        text: "search"
        color: Colours.palette.m3onSurfaceVariant
    }

    TextInput {
        id: searchTextInput

        anchors.left: searchIcon.right
        anchors.leftMargin: Appearance.padding.normal
        anchors.right: clearButton.left
        anchors.rightMargin: Appearance.padding.small
        anchors.verticalCenter: parent.verticalCenter

        color: Colours.palette.m3onSurface
        selectedTextColor: Colours.palette.m3onPrimary
        selectionColor: Colours.palette.m3primary
        font.family: Appearance.font.family.sans
        font.pointSize: Appearance.font.size.large
        clip: true

        Keys.onReturnPressed: launcherSearchBarRoot.accepted()
        Keys.onEnterPressed: launcherSearchBarRoot.accepted()
    }

    StyledText {
        anchors.left: searchTextInput.left
        anchors.verticalCenter: parent.verticalCenter

        visible: searchTextInput.text.length === 0 && !searchTextInput.activeFocus
        text: "Search apps or type > for actions"
        color: Colours.palette.m3onSurfaceVariant
        font.pointSize: Appearance.font.size.large
    }

    IconButton {
        id: clearButton

        anchors.right: parent.right
        anchors.rightMargin: Appearance.padding.small
        anchors.verticalCenter: parent.verticalCenter

        visible: searchTextInput.text.length > 0
        icon: "close"
        type: IconButton.Text

        onClicked: {
            searchTextInput.text = "";
            searchTextInput.forceActiveFocus();
        }
    }

    onLauncherVisibleChanged: {
        if (launcherVisible) {
            searchTextInput.text = "";
            searchTextInput.forceActiveFocus();
        }
    }
}
