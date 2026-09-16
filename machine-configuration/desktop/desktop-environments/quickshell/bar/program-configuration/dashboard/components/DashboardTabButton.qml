import Quickshell.Widgets
import QtQuick
import QtQuick.Controls
import ".."

TabButton {
    id: dashboardTabButtonRoot

    signal selectionRequested(int index)

    required property string iconName
    readonly property bool isCurrentTab: TabBar.tabBar.currentItem === this

    background: null

    contentItem: MouseArea {
        id: tabButtonMouseArea

        implicitWidth: Math.max(tabButtonIcon.width, tabButtonLabel.width)
        implicitHeight: tabButtonIcon.height + tabButtonLabel.height

        cursorShape: Qt.PointingHandCursor

        onPressed: mouse => {
            dashboardTabButtonRoot.selectionRequested(dashboardTabButtonRoot.TabBar.index);

            const stateWrapperY = tabButtonStateWrapper.y;
            tabRippleAnimation.x = mouse.x;
            tabRippleAnimation.y = mouse.y - stateWrapperY;

            const distanceSquared = (offsetX, offsetY) => offsetX * offsetX + offsetY * offsetY;
            tabRippleAnimation.radius = Math.sqrt(Math.max(distanceSquared(mouse.x, mouse.y + stateWrapperY), distanceSquared(mouse.x, tabButtonStateWrapper.height - mouse.y), distanceSquared(width - mouse.x, mouse.y + stateWrapperY), distanceSquared(width - mouse.x, tabButtonStateWrapper.height - mouse.y)));

            tabRippleAnimation.restart();
        }

        onWheel: wheel => {
            if (wheel.angleDelta.y < 0)
                dashboardTabButtonRoot.selectionRequested(Math.min(dashboardTabButtonRoot.TabBar.tabBar.currentIndex + 1, dashboardTabButtonRoot.TabBar.tabBar.count - 1));
            else if (wheel.angleDelta.y > 0)
                dashboardTabButtonRoot.selectionRequested(Math.max(dashboardTabButtonRoot.TabBar.tabBar.currentIndex - 1, 0));
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
