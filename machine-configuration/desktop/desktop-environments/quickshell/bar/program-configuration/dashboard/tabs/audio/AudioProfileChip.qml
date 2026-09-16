pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick
import QtQuick.Layouts

StyledRect {
    id: audioProfileChipRoot

    property string profileName
    property string profileDescription
    property bool profileIsActive: false

    signal activated

    implicitWidth: audioProfileChipLabel.implicitWidth + Appearance.padding.normal * 2
    implicitHeight: audioProfileChipLabel.implicitHeight + Appearance.padding.smaller * 2
    radius: Appearance.rounding.full
    color: profileIsActive ? Colours.palette.m3primary : Colours.palette.m3secondaryContainer

    StyledText {
        id: audioProfileChipLabel

        anchors.centerIn: parent
        text: audioProfileChipRoot.profileDescription
        font.pointSize: Appearance.font.size.smaller
        font.weight: audioProfileChipRoot.profileIsActive ? Font.Medium : Font.Normal
        color: audioProfileChipRoot.profileIsActive ? Colours.palette.m3onPrimary : Colours.palette.m3onSecondaryContainer
    }

    StateLayer {
        color: audioProfileChipRoot.profileIsActive ? Colours.palette.m3onPrimary : Colours.palette.m3onSecondaryContainer
        function onClicked(): void {
            audioProfileChipRoot.activated();
        }
    }
}
