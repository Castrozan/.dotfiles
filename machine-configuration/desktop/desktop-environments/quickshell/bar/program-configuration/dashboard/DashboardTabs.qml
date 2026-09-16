pragma ComponentBehavior: Bound

import "components"
import "."
import Quickshell.Widgets
import QtQuick
import QtQuick.Controls

Item {
    id: dashboardTabsRoot

    required property real nonAnimatedWidth
    property int currentTabIndex: 0
    readonly property alias tabCount: dashboardTabBar.count

    implicitHeight: dashboardTabBar.implicitHeight + tabIndicator.implicitHeight + tabIndicator.anchors.topMargin + tabSeparator.implicitHeight

    TabBar {
        id: dashboardTabBar

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top

        background: null

        onCurrentIndexChanged: dashboardTabsRoot.currentTabIndex = currentIndex

        DashboardTabButton {
            onSelectionRequested: index => dashboardTabsRoot.currentTabIndex = index
            iconName: "dashboard"
            text: "Dashboard"
        }

        DashboardTabButton {
            onSelectionRequested: index => dashboardTabsRoot.currentTabIndex = index
            iconName: "queue_music"
            text: "Media"
        }

        DashboardTabButton {
            onSelectionRequested: index => dashboardTabsRoot.currentTabIndex = index
            iconName: "speed"
            text: "Performance"
        }

        DashboardTabButton {
            onSelectionRequested: index => dashboardTabsRoot.currentTabIndex = index
            iconName: "cloud"
            text: "Weather"
        }

        DashboardTabButton {
            onSelectionRequested: index => dashboardTabsRoot.currentTabIndex = index
            iconName: "headphones"
            text: "Audio"
        }
    }

    Binding {
        target: dashboardTabBar
        property: "currentIndex"
        value: dashboardTabsRoot.currentTabIndex
    }

    Item {
        id: tabIndicator

        anchors.top: dashboardTabBar.bottom
        anchors.topMargin: DashboardConfig.sizes.tabIndicatorSpacing

        implicitWidth: dashboardTabBar.currentItem.implicitWidth
        implicitHeight: 3

        x: {
            const currentTab = dashboardTabBar.currentItem;
            const tabWidth = (dashboardTabsRoot.nonAnimatedWidth - dashboardTabBar.spacing * (dashboardTabBar.count - 1)) / dashboardTabBar.count;
            return tabWidth * currentTab.TabBar.index + (tabWidth - currentTab.implicitWidth) / 2;
        }

        clip: true

        StyledRect {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            implicitHeight: parent.implicitHeight * 2

            color: Colours.palette.m3primary
            radius: Appearance.rounding.full
        }

        Behavior on x {
            Anim {}
        }

        Behavior on implicitWidth {
            Anim {}
        }
    }

    StyledRect {
        id: tabSeparator

        anchors.top: tabIndicator.bottom
        anchors.left: parent.left
        anchors.right: parent.right

        implicitHeight: 1
        color: Colours.palette.m3outlineVariant
    }
}
