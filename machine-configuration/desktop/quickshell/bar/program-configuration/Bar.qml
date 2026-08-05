import Quickshell.Hyprland
import QtQuick
import QtQuick.Layouts
import "modules" as Modules

ColumnLayout {
    id: barRoot

    required property var screenScope

    spacing: 2

    readonly property bool hasHoveredPopoutIcon: collapsedStatusIconsTriggerButton.visible
        ? collapsedStatusIconsTriggerButton.isHovered
        : inlineStatusIconsModule.hasHoveredPopoutIcon
    property var statusIconPositions: ({})

    readonly property real fullStatusIconsImpliedHeight: 6 * 28 + 5 * 2 + 4
    readonly property real minimumRunningAppsAllocation: 30
    readonly property real fixedModulesHeightExcludingStatusIcons:
        launcherButton.implicitHeight +
        windowSwitcherButton.implicitHeight +
        workspacesModule.implicitHeight +
        systemMonitorTopDivider.implicitHeight + systemMonitorTopDivider.Layout.topMargin + systemMonitorTopDivider.Layout.bottomMargin +
        systemMonitorModule.implicitHeight +
        runningAppsTopDivider.implicitHeight + runningAppsTopDivider.Layout.topMargin + runningAppsTopDivider.Layout.bottomMargin +
        minimumRunningAppsAllocation +
        trayModule.implicitHeight +
        clockTopDivider.implicitHeight + clockTopDivider.Layout.topMargin + clockTopDivider.Layout.bottomMargin +
        clockModule.implicitHeight +
        statusIconsTopDivider.implicitHeight + statusIconsTopDivider.Layout.topMargin + statusIconsTopDivider.Layout.bottomMargin +
        powerButton.implicitHeight + powerButton.Layout.bottomMargin +
        spacing * 12
    readonly property bool hasRoomForInlineStatusIcons:
        height >= fixedModulesHeightExcludingStatusIcons + fullStatusIconsImpliedHeight

    function checkPopout(mouseY: real): void {
        let localY = mapFromItem(parent, 0, mouseY).y;

        for (let iconName in statusIconPositions) {
            let pos = statusIconPositions[iconName];
            if (localY >= pos.top && localY <= pos.bottom) {
                if (iconName !== "") {
                    screenScope.showPopout(iconName, mouseY);
                }
                return;
            }
        }
    }

    function handleWheel(mouseY: real, angleDelta: point): void {
        let localY = mapFromItem(parent, 0, mouseY).y;
        let workspacesTop = workspacesModule.y;
        let workspacesBottom = workspacesModule.y + workspacesModule.height;

        if (localY >= workspacesTop && localY <= workspacesBottom) {
            if (angleDelta.y > 0) {
                Hyprland.dispatch("workspace m-1");
            } else if (angleDelta.y < 0) {
                Hyprland.dispatch("workspace m+1");
            }
        }
    }

    function registerStatusIconPosition(name: string, top: real, bottom: real): void {
        let positions = statusIconPositions;
        positions[name] = { top: top, bottom: bottom };
        statusIconPositions = positions;
    }

    Modules.LauncherButton {
        id: launcherButton
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
        Layout.preferredHeight: 40
        screenScope: barRoot.screenScope
    }

    Modules.WindowSwitcherButton {
        id: windowSwitcherButton
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
        Layout.preferredHeight: 32
    }

    Modules.WorkspacesModule {
        id: workspacesModule
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
    }

    Rectangle {
        id: systemMonitorTopDivider
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 4
        Layout.bottomMargin: 4
        width: 20
        implicitHeight: 1
        color: ThemeColors.dim
    }

    Modules.SystemMonitorModule {
        id: systemMonitorModule
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
    }

    Rectangle {
        id: runningAppsTopDivider
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 4
        Layout.bottomMargin: 4
        width: 20
        implicitHeight: 1
        color: ThemeColors.dim
    }

    Modules.RunningAppsModule {
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
        Layout.fillHeight: true
        Layout.preferredHeight: 0
        Layout.minimumHeight: 0
    }

    Modules.TrayModule {
        id: trayModule
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
        screenScope: barRoot.screenScope
    }

    Rectangle {
        id: clockTopDivider
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 4
        Layout.bottomMargin: 4
        width: 20
        implicitHeight: 1
        color: ThemeColors.dim
    }

    Modules.ClockModule {
        id: clockModule
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
    }

    Rectangle {
        id: statusIconsTopDivider
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 4
        Layout.bottomMargin: 4
        width: 20
        implicitHeight: 1
        color: ThemeColors.dim
    }

    Modules.StatusIconsModule {
        id: inlineStatusIconsModule
        visible: barRoot.hasRoomForInlineStatusIcons
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40

        barRoot: barRoot
        screenScope: barRoot.screenScope
    }

    Modules.StatusIconsTriggerButton {
        id: collapsedStatusIconsTriggerButton
        visible: !barRoot.hasRoomForInlineStatusIcons
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        Layout.topMargin: 4

        barRoot: barRoot
        screenScope: barRoot.screenScope
    }

    Modules.PowerButton {
        id: powerButton
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
        Layout.preferredHeight: 40
        Layout.bottomMargin: 4
    }
}
