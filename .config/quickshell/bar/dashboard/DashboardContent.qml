pragma ComponentBehavior: Bound

import "components"
import "tabs"
import "."
import QtQuick
import QtQuick.Layouts

Item {
    id: dashboardContentRoot

    property int currentTabIndex: 0
    readonly property real nonAnimatedWidth: tabsFlickable.implicitWidth + flickableWrapper.anchors.margins * 2
    readonly property real nonAnimatedHeight: dashboardTabsBar.implicitHeight + dashboardTabsBar.anchors.topMargin + tabsFlickable.implicitHeight + flickableWrapper.anchors.margins * 2

    implicitWidth: nonAnimatedWidth
    implicitHeight: nonAnimatedHeight

    DashboardTabs {
        id: dashboardTabsBar

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: Appearance.padding.normal
        anchors.margins: Appearance.padding.large

        nonAnimatedWidth: dashboardContentRoot.nonAnimatedWidth - anchors.margins * 2
        currentTabIndex: dashboardContentRoot.currentTabIndex

        onCurrentTabIndexChanged: dashboardContentRoot.currentTabIndex = currentTabIndex
    }

    Item {
        id: flickableWrapper

        anchors.top: dashboardTabsBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: Appearance.padding.large

        clip: true

        Flickable {
            id: tabsFlickable

            readonly property list<Item> tabPanes: [tabPane0, tabPane1, tabPane2, tabPane3]
            readonly property Item currentTabItem: tabPanes[dashboardContentRoot.currentTabIndex]

            anchors.fill: parent

            flickableDirection: Flickable.HorizontalFlick

            implicitWidth: currentTabItem.implicitWidth
            implicitHeight: currentTabItem.implicitHeight

            contentX: currentTabItem.x
            contentWidth: tabsRow.implicitWidth
            contentHeight: height

            onContentXChanged: {
                if (!moving)
                    return;

                const offsetX = contentX - currentTabItem.x;
                if (offsetX > currentTabItem.implicitWidth / 2)
                    dashboardContentRoot.currentTabIndex = Math.min(dashboardContentRoot.currentTabIndex + 1, dashboardTabsBar.tabCount - 1);
                else if (offsetX < -currentTabItem.implicitWidth / 2)
                    dashboardContentRoot.currentTabIndex = Math.max(dashboardContentRoot.currentTabIndex - 1, 0);
            }

            onDragEnded: {
                const offsetX = contentX - currentTabItem.x;
                if (offsetX > currentTabItem.implicitWidth / 10)
                    dashboardContentRoot.currentTabIndex = Math.min(dashboardContentRoot.currentTabIndex + 1, dashboardTabsBar.tabCount - 1);
                else if (offsetX < -currentTabItem.implicitWidth / 10)
                    dashboardContentRoot.currentTabIndex = Math.max(dashboardContentRoot.currentTabIndex - 1, 0);
                else
                    contentX = Qt.binding(() => currentTabItem.x);
            }

            RowLayout {
                id: tabsRow

                Loader {
                    id: tabPane0
                    active: true
                    Layout.alignment: Qt.AlignTop
                    sourceComponent: DashboardTab {}
                }

                Loader {
                    id: tabPane1
                    active: true
                    Layout.alignment: Qt.AlignTop
                    sourceComponent: MediaTab {}
                }

                Loader {
                    id: tabPane2
                    active: true
                    Layout.alignment: Qt.AlignTop
                    sourceComponent: PerformanceTab {}
                }

                Loader {
                    id: tabPane3
                    active: true
                    Layout.alignment: Qt.AlignTop
                    sourceComponent: WeatherTab {}
                }
            }

            Behavior on contentX {
                Anim {}
            }
        }
    }
}
