pragma ComponentBehavior: Bound

import "../components"
import "../services"
import ".."
import QtQuick

Row {
    id: userWidgetRoot

    padding: Appearance.padding.large
    spacing: Appearance.spacing.normal

    StyledClippingRect {
        implicitWidth: userInfoColumn.implicitHeight
        implicitHeight: userInfoColumn.implicitHeight

        radius: Appearance.rounding.large
        color: Colours.layer(Colours.palette.m3surfaceContainerHigh, 2)

        MaterialIcon {
            anchors.centerIn: parent

            text: "person"
            fill: 1
            grade: 200
            font.pointSize: Math.floor(userInfoColumn.implicitHeight / 2) || 1
        }

        Image {
            anchors.fill: parent
            source: SysInfoService.faceIconPath
            asynchronous: true
            fillMode: Image.PreserveAspectCrop
            visible: status === Image.Ready
        }
    }

    Column {
        id: userInfoColumn

        anchors.verticalCenter: parent.verticalCenter
        spacing: Appearance.spacing.normal

        UserInfoLine {
            iconName: "deployed_code"
            infoText: SysInfoService.osPrettyName || SysInfoService.osName
            lineColor: Colours.palette.m3primary
        }

        UserInfoLine {
            iconName: "select_window_2"
            infoText: SysInfoService.windowManager
            lineColor: Colours.palette.m3secondary
        }

        UserInfoLine {
            iconName: "timer"
            infoText: `up ${SysInfoService.uptime}`
            lineColor: Colours.palette.m3tertiary
        }
    }

    component UserInfoLine: Item {
        id: userInfoLineRoot

        required property string iconName
        required property string infoText
        required property color lineColor

        implicitWidth: lineIcon.implicitWidth + lineText.implicitWidth + lineText.anchors.leftMargin
        implicitHeight: Math.max(lineIcon.implicitHeight, lineText.implicitHeight)

        MaterialIcon {
            id: lineIcon

            anchors.left: parent.left
            fill: 1
            text: userInfoLineRoot.iconName
            color: userInfoLineRoot.lineColor
            font.pointSize: Appearance.font.size.normal
        }

        StyledText {
            id: lineText

            anchors.verticalCenter: lineIcon.verticalCenter
            anchors.left: lineIcon.right
            anchors.leftMargin: Appearance.spacing.small
            text: `:  ${userInfoLineRoot.infoText}`
            font.pointSize: Appearance.font.size.normal
            elide: Text.ElideRight
        }
    }
}
