pragma ComponentBehavior: Bound

import ".."
import QtQuick

MouseArea {
    id: stateLayerRoot

    property bool disabled
    property bool showHoverBackground: true
    property color color: Colours.palette.m3onSurface
    property real radius: parent?.radius ?? 0
    property alias rect: hoverBackgroundLayer

    function onClicked(): void {
    }

    anchors.fill: parent

    enabled: !disabled
    cursorShape: disabled ? undefined : Qt.PointingHandCursor
    hoverEnabled: true

    onPressed: event => {
        if (disabled)
            return;

        rippleAnimation.x = event.x;
        rippleAnimation.y = event.y;

        const distanceSquared = (originX, originY) => originX * originX + originY * originY;
        rippleAnimation.radius = Math.sqrt(Math.max(
            distanceSquared(event.x, event.y),
            distanceSquared(event.x, height - event.y),
            distanceSquared(width - event.x, event.y),
            distanceSquared(width - event.x, height - event.y)
        ));

        rippleAnimation.restart();
    }

    onClicked: event => !disabled && onClicked(event)

    SequentialAnimation {
        id: rippleAnimation

        property real x
        property real y
        property real radius

        PropertyAction {
            target: rippleCircle
            property: "x"
            value: rippleAnimation.x
        }
        PropertyAction {
            target: rippleCircle
            property: "y"
            value: rippleAnimation.y
        }
        PropertyAction {
            target: rippleCircle
            property: "opacity"
            value: 0.08
        }
        Anim {
            target: rippleCircle
            properties: "implicitWidth,implicitHeight"
            from: 0
            to: rippleAnimation.radius * 2
            easing.bezierCurve: Appearance.anim.curves.standardDecel
        }
        Anim {
            target: rippleCircle
            property: "opacity"
            to: 0
        }
    }

    StyledClippingRect {
        id: hoverBackgroundLayer

        anchors.fill: parent

        color: Qt.alpha(stateLayerRoot.color, stateLayerRoot.disabled ? 0 : stateLayerRoot.pressed ? 0.12 : (stateLayerRoot.showHoverBackground && stateLayerRoot.containsMouse) ? 0.08 : 0)
        radius: stateLayerRoot.radius

        StyledRect {
            id: rippleCircle

            radius: Appearance.rounding.full
            color: stateLayerRoot.color
            opacity: 0

            transform: Translate {
                x: -rippleCircle.width / 2
                y: -rippleCircle.height / 2
            }
        }
    }
}
