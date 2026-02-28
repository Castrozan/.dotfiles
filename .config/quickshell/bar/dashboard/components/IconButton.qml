pragma ComponentBehavior: Bound

import ".."
import QtQuick

StyledRect {
    id: iconButtonRoot

    enum Type {
        Filled,
        Tonal,
        Text
    }

    property alias icon: iconLabel.text
    property bool checked
    property bool toggle
    property real padding: type === IconButton.Text ? Appearance.padding.small / 2 : Appearance.padding.smaller
    property alias font: iconLabel.font
    property int type: IconButton.Filled
    property bool disabled

    property alias stateLayer: iconButtonStateLayer
    property alias label: iconLabel
    property alias radiusAnimation: iconButtonRadiusAnimation

    property bool internalChecked
    property color activeColour: type === IconButton.Filled ? Colours.palette.m3primary : Colours.palette.m3secondary
    property color inactiveColour: {
        if (!toggle && type === IconButton.Filled)
            return Colours.palette.m3primary;
        return type === IconButton.Filled ? Colours.tPalette.m3surfaceContainer : Colours.palette.m3secondaryContainer;
    }
    property color activeOnColour: type === IconButton.Filled ? Colours.palette.m3onPrimary : type === IconButton.Tonal ? Colours.palette.m3onSecondary : Colours.palette.m3primary
    property color inactiveOnColour: {
        if (!toggle && type === IconButton.Filled)
            return Colours.palette.m3onPrimary;
        return type === IconButton.Tonal ? Colours.palette.m3onSecondaryContainer : Colours.palette.m3onSurfaceVariant;
    }
    property color disabledColour: Qt.alpha(Colours.palette.m3onSurface, 0.1)
    property color disabledOnColour: Qt.alpha(Colours.palette.m3onSurface, 0.38)

    signal clicked

    onCheckedChanged: internalChecked = checked

    radius: internalChecked ? Appearance.rounding.small : implicitHeight / 2 * Math.min(1, Appearance.rounding.scale)
    color: type === IconButton.Text ? "transparent" : disabled ? disabledColour : internalChecked ? activeColour : inactiveColour

    implicitWidth: implicitHeight
    implicitHeight: iconLabel.implicitHeight + padding * 2

    StateLayer {
        id: iconButtonStateLayer

        color: iconButtonRoot.internalChecked ? iconButtonRoot.activeOnColour : iconButtonRoot.inactiveOnColour
        disabled: iconButtonRoot.disabled

        function onClicked(): void {
            if (iconButtonRoot.toggle)
                iconButtonRoot.internalChecked = !iconButtonRoot.internalChecked;
            iconButtonRoot.clicked();
        }
    }

    MaterialIcon {
        id: iconLabel

        anchors.centerIn: parent
        color: iconButtonRoot.disabled ? iconButtonRoot.disabledOnColour : iconButtonRoot.internalChecked ? iconButtonRoot.activeOnColour : iconButtonRoot.inactiveOnColour
        fill: !iconButtonRoot.toggle || iconButtonRoot.internalChecked ? 1 : 0

        Behavior on fill {
            Anim {}
        }
    }

    Behavior on radius {
        Anim {
            id: iconButtonRadiusAnimation
        }
    }
}
