pragma ComponentBehavior: Bound

import "../dashboard/components"
import "../dashboard"
import ".."
import "."
import QtQuick

Item {
    id: launcherContentRoot

    property bool launcherVisible: false

    implicitWidth: LauncherConfig.contentWidth + Appearance.padding.large * 2
    implicitHeight: resultsList.implicitHeight + Appearance.spacing.normal + LauncherConfig.searchBarHeight + Appearance.padding.large * 2

    Column {
        id: contentColumn

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: Appearance.padding.large
        spacing: Appearance.spacing.normal

        LauncherResultsList {
            id: resultsList

            width: parent.width

            searchText: searchBar.searchText

            onItemActivated: launcherContentRoot.launcherVisible = false
        }

        LauncherSearchBar {
            id: searchBar

            width: parent.width

            launcherVisible: launcherContentRoot.launcherVisible

            onAccepted: resultsList.activateCurrentItem()

            Keys.onUpPressed: resultsList.moveSelectionUp()
            Keys.onDownPressed: resultsList.moveSelectionDown()
        }
    }

    Keys.onEscapePressed: launcherContentRoot.launcherVisible = false

    Keys.forwardTo: [searchBar]
}
