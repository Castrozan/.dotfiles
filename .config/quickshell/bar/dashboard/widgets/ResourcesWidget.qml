pragma ComponentBehavior: Bound

import "../components"
import "../services"
import ".."
import QtQuick

Row {
    id: resourcesWidgetRoot

    anchors.top: parent.top
    anchors.bottom: parent.bottom

    padding: Appearance.padding.large
    spacing: Appearance.spacing.normal

    Component.onCompleted: SystemUsageService.refCount++
    Component.onDestruction: SystemUsageService.refCount--

    ResourceBar {
        iconName: "memory"
        value: SystemUsageService.cpuPercentage
        barColor: Colours.palette.m3primary
    }

    ResourceBar {
        iconName: "memory_alt"
        value: SystemUsageService.memoryPercentage
        barColor: Colours.palette.m3secondary
    }

    ResourceBar {
        iconName: "hard_disk"
        value: SystemUsageService.storagePercentage
        barColor: Colours.palette.m3tertiary
    }

    component ResourceBar: Item {
        id: resourceBarRoot

        required property string iconName
        required property real value
        required property color barColor

        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Appearance.padding.large
        implicitWidth: resourceBarIcon.implicitWidth

        StyledRect {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.bottom: resourceBarIcon.top
            anchors.bottomMargin: Appearance.spacing.small

            implicitWidth: 6

            color: Colours.layer(Colours.palette.m3surfaceContainerHigh, 2)
            radius: Appearance.rounding.full

            StyledRect {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                implicitHeight: resourceBarRoot.value * parent.height

                color: resourceBarRoot.barColor
                radius: Appearance.rounding.full
            }
        }

        MaterialIcon {
            id: resourceBarIcon

            anchors.bottom: parent.bottom

            text: resourceBarRoot.iconName
            color: resourceBarRoot.barColor
        }

        Behavior on value {
            Anim {
                duration: Appearance.anim.durations.large
            }
        }
    }
}
