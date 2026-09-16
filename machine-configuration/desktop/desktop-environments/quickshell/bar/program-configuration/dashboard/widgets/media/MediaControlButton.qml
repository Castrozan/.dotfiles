pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick
import QtQuick.Layouts

StyledRect {
    id: mediaControlButtonRoot

    required property string iconName
    required property bool canUse
    function onClicked(): void {
    }

    implicitWidth: Math.max(controlButtonIcon.implicitHeight, controlButtonIcon.implicitHeight) + Appearance.padding.small
    implicitHeight: implicitWidth

    StateLayer {
        disabled: !mediaControlButtonRoot.canUse
        radius: Appearance.rounding.full

        function onClicked(): void {
            mediaControlButtonRoot.onClicked();
        }
    }

    MaterialIcon {
        id: controlButtonIcon

        anchors.centerIn: parent
        anchors.verticalCenterOffset: font.pointSize * 0.05

        animate: true
        text: mediaControlButtonRoot.iconName
        color: mediaControlButtonRoot.canUse ? Colours.palette.m3onSurface : Colours.palette.m3outline
        font.pointSize: Appearance.font.size.large
    }
}
