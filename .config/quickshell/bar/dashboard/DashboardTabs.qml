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

        currentIndex: dashboardTabsRoot.currentTabIndex
        background: null

        onCurrentIndexChanged: dashboardTabsRoot.currentTabIndex = currentIndex

        DashboardTabButton {
            iconName: "dashboard"
            text: "Dashboard"
        }

        DashboardTabButton {
            iconName: "queue_music"
            text: "Media"
        }

        DashboardTabButton {
            iconName: "speed"
            text: "Performance"
        }

        DashboardTabButton {
            iconName: "cloud"
            text: "Weather"
        }
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

    component DashboardTabButton: TabButton {
        id: dashboardTabButtonRoot

        required property string iconName
        readonly property bool isCurrentTab: TabBar.tabBar.currentItem === this

        background: null

        contentItem: MouseArea {
            id: tabButtonMouseArea

            implicitWidth: Math.max(tabButtonIcon.width, tabButtonLabel.width)
            implicitHeight: tabButtonIcon.height + tabButtonLabel.height

            cursorShape: Qt.PointingHandCursor

            onPressed: mouse => {
                dashboardTabsRoot.currentTabIndex = dashboardTabButtonRoot.TabBar.index;

                const stateWrapperY = tabButtonStateWrapper.y;
                tabRippleAnimation.x = mouse.x;
                tabRippleAnimation.y = mouse.y - stateWrapperY;

                const distanceSquared = (offsetX, offsetY) => offsetX * offsetX + offsetY * offsetY;
                tabRippleAnimation.radius = Math.sqrt(Math.max(distanceSquared(mouse.x, mouse.y + stateWrapperY), distanceSquared(mouse.x, tabButtonStateWrapper.height - mouse.y), distanceSquared(width - mouse.x, mouse.y + stateWrapperY), distanceSquared(width - mouse.x, tabButtonStateWrapper.height - mouse.y)));

                tabRippleAnimation.restart();
            }

            onWheel: wheel => {
                if (wheel.angleDelta.y < 0)
                    dashboardTabsRoot.currentTabIndex = Math.min(dashboardTabsRoot.currentTabIndex + 1, dashboardTabBar.count - 1);
                else if (wheel.angleDelta.y > 0)
                    dashboardTabsRoot.currentTabIndex = Math.max(dashboardTabsRoot.currentTabIndex - 1, 0);
            }

            SequentialAnimation {
                id: tabRippleAnimation

                property real x
                property real y
                property real radius

                PropertyAction {
                    target: tabRippleCircle
                    property: "x"
                    value: tabRippleAnimation.x
                }
                PropertyAction {
                    target: tabRippleCircle
                    property: "y"
                    value: tabRippleAnimation.y
                }
                PropertyAction {
                    target: tabRippleCircle
                    property: "opacity"
                    value: 0.08
                }
                Anim {
                    target: tabRippleCircle
                    properties: "implicitWidth,implicitHeight"
                    from: 0
                    to: tabRippleAnimation.radius * 2
                    duration: Appearance.anim.durations.normal
                    easing.bezierCurve: Appearance.anim.curves.standardDecel
                }
                Anim {
                    target: tabRippleCircle
                    property: "opacity"
                    to: 0
                    duration: Appearance.anim.durations.normal
                    easing.type: Easing.BezierSpline
                    easing.bezierCurve: Appearance.anim.curves.standard
                }
            }

            ClippingRectangle {
                id: tabButtonStateWrapper

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                implicitHeight: parent.height + DashboardConfig.sizes.tabIndicatorSpacing * 2

                color: "transparent"
                radius: Appearance.rounding.small

                StyledRect {
                    anchors.fill: parent

                    color: dashboardTabButtonRoot.isCurrentTab ? Colours.palette.m3primary : Colours.palette.m3onSurface
                    opacity: tabButtonMouseArea.pressed ? 0.1 : dashboardTabButtonRoot.hovered ? 0.08 : 0

                    Behavior on opacity {
                        Anim {}
                    }
                }

                StyledRect {
                    id: tabRippleCircle

                    radius: Appearance.rounding.full
                    color: dashboardTabButtonRoot.isCurrentTab ? Colours.palette.m3primary : Colours.palette.m3onSurface
                    opacity: 0

                    transform: Translate {
                        x: -tabRippleCircle.width / 2
                        y: -tabRippleCircle.height / 2
                    }
                }
            }

            MaterialIcon {
                id: tabButtonIcon

                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: tabButtonLabel.top

                text: dashboardTabButtonRoot.iconName
                color: dashboardTabButtonRoot.isCurrentTab ? Colours.palette.m3primary : Colours.palette.m3onSurfaceVariant
                fill: dashboardTabButtonRoot.isCurrentTab ? 1 : 0
                font.pointSize: Appearance.font.size.large

                Behavior on fill {
                    Anim {}
                }
            }

            StyledText {
                id: tabButtonLabel

                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom

                text: dashboardTabButtonRoot.text
                color: dashboardTabButtonRoot.isCurrentTab ? Colours.palette.m3primary : Colours.palette.m3onSurfaceVariant
            }
        }
    }
}
