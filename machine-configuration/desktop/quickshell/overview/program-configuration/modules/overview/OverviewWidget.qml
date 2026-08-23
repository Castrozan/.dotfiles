import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import "../../common"
import "../../services"
import "."

Item {
    id: root
    required property var panelWindow
    readonly property HyprlandMonitor monitor: Hyprland.monitorFor(panelWindow.screen)
    readonly property var toplevels: ToplevelManager.toplevels
    readonly property int effectiveActiveWorkspaceId: Math.max(1, Math.min(100, monitor?.activeWorkspace?.id ?? 1))
    readonly property int workspacesShown: Config.options.overview.rows * Config.options.overview.columns
    readonly property bool useWorkspaceMap: Config.options.overview.useWorkspaceMap
    readonly property var workspaceMap: Config.options.overview.workspaceMap
    readonly property int workspaceOffset: useWorkspaceMap ? Number(workspaceMap[root.monitor?.id] ?? 0) : 0
    readonly property int workspaceGroup: Math.floor((effectiveActiveWorkspaceId - workspaceOffset - 1) / workspacesShown)
    property bool monitorIsFocused: (Hyprland.focusedMonitor?.name == monitor.name)
    property var windows: HyprlandData.windowList
    property var windowByAddress: HyprlandData.windowByAddress
    property var windowAddresses: HyprlandData.addresses
    property var workspaceIds: HyprlandData.workspaceIds
    property var monitorData: HyprlandData.monitors.find(m => m.id === root.monitor?.id)
    property real scale: Config.options.overview.scale
    property color activeBorderColor: Appearance.colors.colSecondary

    property real workspaceImplicitWidth: (monitorData?.transform % 2 === 1) ?
        ((monitor.height / monitor.scale - (monitorData?.reserved?.[0] ?? 0) - (monitorData?.reserved?.[2] ?? 0)) * root.scale) :
        ((monitor.width / monitor.scale - (monitorData?.reserved?.[0] ?? 0) - (monitorData?.reserved?.[2] ?? 0)) * root.scale)
    property real workspaceImplicitHeight: (monitorData?.transform % 2 === 1) ?
        ((monitor.width / monitor.scale - (monitorData?.reserved?.[1] ?? 0) - (monitorData?.reserved?.[3] ?? 0)) * root.scale) :
        ((monitor.height / monitor.scale - (monitorData?.reserved?.[1] ?? 0) - (monitorData?.reserved?.[3] ?? 0)) * root.scale)

    property real workspaceNumberMargin: 80
    property real workspaceNumberSize: Config.options.overview.workspaceNumberBaseSize * monitor.scale
    property int workspaceZ: 0
    property int windowZ: 1
    property int windowDraggingZ: 99999
    property real workspaceSpacing: Config.options.overview.workspaceSpacing
    property bool showSpecialWorkspaces: Config.options.overview.showSpecialWorkspaces
    property var configuredSpecialWorkspaces: Config.options.overview.specialWorkspaces ?? []
    property int specialWorkspaceColumns: Math.max(1, Config.options.overview.specialWorkspaceColumns)
    property real panelOpacity: Math.max(0, Math.min(1, Config.options.overview.effects.panelOpacity))
    property real workspaceOpacity: Math.max(0, Math.min(1, Config.options.overview.effects.workspaceOpacity))
    property bool glassMode: Config.options.overview.effects.glassMode
    property real glassTintStrength: Math.max(0, Math.min(1, Config.options.overview.effects.glassTintStrength))
    property real glassBorderOpacity: Math.max(0, Math.min(1, Config.options.overview.effects.glassBorderOpacity))
    property real glassShineOpacity: Math.max(0, Math.min(1, Config.options.overview.effects.glassShineOpacity))
    property real effectivePanelOpacity: glassMode ? Math.min(panelOpacity, 0.72) : panelOpacity
    property real effectiveWorkspaceOpacity: glassMode ? Math.min(workspaceOpacity, 0.62) : workspaceOpacity

    property int draggingFromWorkspace: -1
    property int draggingTargetWorkspace: -1
    property string draggingTargetSpecialWorkspace: ""
    property int previewRecaptureToken: 0
    property var allWorkspaces: HyprlandData.allWorkspaces
    property bool previewsEnabled: Config.options.overview.previewsEnabled
    property string previewModeRaw: Config.options.overview.previewMode
    property string previewMode: {
        const mode = `${previewModeRaw ?? "live"}`.trim().toLowerCase();
        return (mode === "event" || mode === "snapshot") ? "event" : "live";
    }
    property bool useEventPreviewRefresh: previewsEnabled && previewMode === "event"

    readonly property string createSpecialWorkspaceTarget: "__create_special_workspace__"
    readonly property var workspaceLayout: ({
        rows: Config.options.overview.rows,
        columns: Config.options.overview.columns,
        orderBottomUp: Config.options.overview.orderBottomUp,
        orderRightLeft: Config.options.overview.orderRightLeft,
        workspaceOffset: root.workspaceOffset,
        workspaceGroup: root.workspaceGroup
    })

    function stepWorkspace(delta) {
        if (!Number.isFinite(delta) || delta === 0)
            return;

        const currentId = monitor?.activeWorkspace?.id ?? effectiveActiveWorkspaceId;
        const minWorkspaceId = workspaceOffset + 1;
        let maxWorkspaceId = minWorkspaceId + workspacesShown - 1;
        for (const workspaceId of (workspaceIds ?? [])) {
            if (Number.isFinite(workspaceId) && workspaceId >= minWorkspaceId) {
                maxWorkspaceId = Math.max(maxWorkspaceId, workspaceId);
            }
        }
        maxWorkspaceId = Math.max(maxWorkspaceId, currentId);

        let targetId = currentId + delta;
        if (targetId < minWorkspaceId) {
            targetId = maxWorkspaceId;
        } else if (targetId > maxWorkspaceId) {
            targetId = minWorkspaceId;
        }
        Hyprland.dispatch(`workspace ${targetId}`);
    }

    implicitWidth: overviewBackground.implicitWidth + Appearance.sizes.elevationMargin * 2
    implicitHeight: overviewBackground.implicitHeight + Appearance.sizes.elevationMargin * 2

    property Component windowComponent: OverviewWindow {}
    property list<OverviewWindow> windowWidgets: []

    OverviewSpecialWorkspaceModel {
        id: specialWorkspaces
        monitor: root.monitor
        windowByAddress: root.windowByAddress
        allWorkspaces: root.allWorkspaces
        configuredSpecialWorkspaces: root.configuredSpecialWorkspaces
        showSpecialWorkspaces: root.showSpecialWorkspaces
        columnCount: root.specialWorkspaceColumns
        scale: root.scale
        workspaceSpacing: root.workspaceSpacing
        tileHeight: root.workspaceImplicitHeight
        sectionWidth: workspaceGrid.implicitWidth
        workspaceGridHeight: workspaceGrid.implicitHeight
    }

    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (!GlobalStates.overviewOpen || !root.useEventPreviewRefresh)
                return;

            const eventName = `${event?.name ?? event?.event ?? event?.type ?? ""}`;
            if (eventName === "closewindow" || eventName === "openwindow" || eventName === "movewindow") {
                root.previewRecaptureToken += 1;
            }
        }
    }

    StyledRectangularShadow {
        target: overviewBackground
    }
    Rectangle { // Background
        id: overviewBackground
        property real padding: Config.options.overview.backgroundPadding
        anchors.fill: parent
        anchors.margins: Appearance.sizes.elevationMargin

        implicitWidth: contentLayout.implicitWidth + padding * 2
        implicitHeight: contentLayout.implicitHeight + padding * 2
        radius: Appearance.rounding.screenRounding * root.scale + padding
        clip: true
        color: ColorUtils.applyAlpha(
            root.glassMode
                ? ColorUtils.mix(Appearance.colors.colLayer0, Appearance.colors.colLayer1, 0.78 - root.glassTintStrength * 0.35)
                : Appearance.colors.colLayer0,
            root.effectivePanelOpacity
        )
        border.width: 1
        border.color: ColorUtils.applyAlpha(
            root.glassMode
                ? ColorUtils.mix(Appearance.colors.colLayer0Border, Appearance.m3colors.m3outline, 0.52)
                : Appearance.colors.colLayer0Border,
            root.glassMode ? root.glassBorderOpacity : root.effectivePanelOpacity
        )

        Rectangle {
            visible: root.glassMode
            anchors.fill: parent
            radius: parent.radius
            color: "transparent"
            gradient: Gradient {
                GradientStop { position: 0.0; color: ColorUtils.applyAlpha("#FFFFFF", root.glassShineOpacity * 0.35) }
                GradientStop { position: 0.42; color: ColorUtils.applyAlpha("#FFFFFF", 0.0) }
                GradientStop { position: 1.0; color: ColorUtils.applyAlpha("#000000", root.glassShineOpacity * 0.22) }
            }
        }

        Rectangle {
            visible: root.glassMode
            anchors.fill: parent
            anchors.margins: 1
            radius: Math.max(parent.radius - 1, 0)
            color: "transparent"
            border.width: 1
            border.color: ColorUtils.applyAlpha("#FFFFFF", root.glassBorderOpacity * 0.20)
        }

        ColumnLayout { // Workspaces
            id: contentLayout

            z: root.workspaceZ
            anchors.centerIn: parent
            spacing: root.workspaceSpacing

            OverviewWorkspaceGrid {
                id: workspaceGrid
                workspaceLayout: root.workspaceLayout
                windowByAddress: root.windowByAddress
                activeWorkspaceId: root.effectiveActiveWorkspaceId
                workspaceSpacing: root.workspaceSpacing
                workspaceImplicitWidth: root.workspaceImplicitWidth
                workspaceImplicitHeight: root.workspaceImplicitHeight
                workspaceNumberSize: root.workspaceNumberSize
                scale: root.scale
                glassMode: root.glassMode
                glassShineOpacity: root.glassShineOpacity
                glassBorderOpacity: root.glassBorderOpacity
                effectiveWorkspaceOpacity: root.effectiveWorkspaceOpacity
                draggingFromWorkspace: root.draggingFromWorkspace
                draggingTargetWorkspace: root.draggingTargetWorkspace
                onDragTargetEntered: workspaceId => {
                    root.draggingTargetWorkspace = workspaceId;
                    root.draggingTargetSpecialWorkspace = "";
                }
                onDragTargetExited: workspaceId => {
                    if (root.draggingTargetWorkspace === workspaceId)
                        root.draggingTargetWorkspace = -1;
                }
            }

            Item {
                visible: root.showSpecialWorkspaces && specialWorkspaces.hasSpecialWorkspaceSection
                implicitWidth: 1
                implicitHeight: specialWorkspaces.stripGap
            }

            OverviewSpecialWorkspaceStrip {
                visible: root.showSpecialWorkspaces && specialWorkspaces.hasSpecialWorkspaceSection
                specialWorkspaceModel: specialWorkspaces
                monitor: root.monitor
                widgetMonitorData: root.monitorData
                windowByAddress: root.windowByAddress
                windowDragLayer: specialWindowDragLayer
                scale: root.scale
                workspaceSpacing: root.workspaceSpacing
                workspaceImplicitWidth: root.workspaceImplicitWidth
                workspaceImplicitHeight: root.workspaceImplicitHeight
                glassMode: root.glassMode
                glassBorderOpacity: root.glassBorderOpacity
                effectivePanelOpacity: root.effectivePanelOpacity
                effectiveWorkspaceOpacity: root.effectiveWorkspaceOpacity
                activeBorderColor: root.activeBorderColor
                createSpecialWorkspaceTarget: root.createSpecialWorkspaceTarget
                draggingTargetWorkspace: root.draggingTargetWorkspace
                draggingTargetSpecialWorkspace: root.draggingTargetSpecialWorkspace
                windowDraggingZ: root.windowDraggingZ
                previewRecaptureToken: root.previewRecaptureToken
                onDragTargetEntered: specialWorkspaceName => {
                    root.draggingTargetWorkspace = -1;
                    root.draggingTargetSpecialWorkspace = specialWorkspaceName;
                }
                onDragTargetExited: specialWorkspaceName => {
                    if (root.draggingTargetSpecialWorkspace === specialWorkspaceName)
                        root.draggingTargetSpecialWorkspace = "";
                }
                onWindowDragStarted: {
                    root.draggingFromWorkspace = -1;
                    root.draggingTargetSpecialWorkspace = "";
                }
                onWindowDragFinished: {
                    root.draggingFromWorkspace = -1;
                    root.draggingTargetWorkspace = -1;
                    root.draggingTargetSpecialWorkspace = "";
                }
            }
        }

        Item { // Windows & focused workspace indicator
            id: windowSpace
            anchors.centerIn: parent
            implicitWidth: contentLayout.implicitWidth
            implicitHeight: contentLayout.implicitHeight

            WheelHandler {
                target: null
                acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                onWheel: event => {
                    const deltaY = event.angleDelta.y;
                    if (!deltaY)
                        return;
                    root.stepWorkspace(deltaY > 0 ? -1 : 1);
                    event.accepted = true;
                }
            }

            Repeater { // Window repeater
                model: ScriptModel {
                    values: {
                        return ToplevelManager.toplevels.values.filter((toplevel) => {
                            const address = `0x${toplevel.HyprlandToplevel.address}`
                            var win = windowByAddress[address]
                            if (specialWorkspaces.isSpecialWorkspace(win))
                                return false;
                            const minWorkspace = root.workspaceGroup * root.workspacesShown + 1 + workspaceOffset;
                            const maxWorkspace = (root.workspaceGroup + 1) * root.workspacesShown + workspaceOffset;
                            const inWorkspaceGroup = (minWorkspace <= win?.workspace?.id && win?.workspace?.id <= maxWorkspace)
                            return inWorkspaceGroup;
                        }).sort((a, b) => {
                            // Proper stacking order based on Hyprland's window properties
                            const addrA = `0x${a.HyprlandToplevel.address}`
                            const addrB = `0x${b.HyprlandToplevel.address}`
                            const winA = windowByAddress[addrA]
                            const winB = windowByAddress[addrB]

                            // 1. Pinned windows are always on top
                            if (winA?.pinned !== winB?.pinned) {
                                return winA?.pinned ? 1 : -1
                            }

                            // 2. Floating windows above tiled windows
                            if (winA?.floating !== winB?.floating) {
                                return winA?.floating ? 1 : -1
                            }

                            // 3. Within same category, sort by focus history
                            // Lower focusHistoryID = more recently focused = higher in stack
                            return (winB?.focusHistoryID ?? 0) - (winA?.focusHistoryID ?? 0)
                        })
                    }
                }
                delegate: OverviewWindow {
                    id: window
                    required property var modelData
                    required property int index
                    property int monitorId: windowData?.monitor
                    property var monitor: HyprlandData.monitors.find(m => m.id === monitorId)
                    property var address: `0x${modelData.HyprlandToplevel.address}`
                    windowData: windowByAddress[address]
                    toplevel: modelData
                    monitorData: monitor
                    widgetMonitorData: root.monitorData
                    scale: root.scale
                    availableWorkspaceWidth: root.workspaceImplicitWidth
                    availableWorkspaceHeight: root.workspaceImplicitHeight
                    widgetMonitorId: root.monitor.id
                    recaptureToken: root.previewRecaptureToken

                    property bool atInitPosition: (initX == x && initY == y)

                    property int workspaceColIndex: OverviewWorkspaceMath.workspaceColumn(windowData?.workspace.id, root.workspaceLayout)
                    property int workspaceRowIndex: OverviewWorkspaceMath.workspaceRow(windowData?.workspace.id, root.workspaceLayout)
                    xOffset: (root.workspaceImplicitWidth + workspaceSpacing) * workspaceColIndex
                    yOffset: (root.workspaceImplicitHeight + workspaceSpacing) * workspaceRowIndex

                    Timer {
                        id: updateWindowPosition
                        interval: Config.options.hacks.arbitraryRaceConditionDelay
                        repeat: false
                        running: false
                        onTriggered: {
                            window.x = Math.round(Math.max((windowData?.at[0] - (monitor?.x ?? 0) - (monitorData?.reserved?.[0] ?? 0)) * root.scale * window.widthRatio, 0) + xOffset)
                            window.y = Math.round(Math.max((windowData?.at[1] - (monitor?.y ?? 0) - (monitorData?.reserved?.[1] ?? 0)) * root.scale * window.heightRatio, 0) + yOffset)
                        }
                    }

                    z: atInitPosition ? (root.windowZ + index) : root.windowDraggingZ
                    Drag.hotSpot.x: targetWindowWidth / 2
                    Drag.hotSpot.y: targetWindowHeight / 2
                    MouseArea {
                        id: dragArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onEntered: hovered = true
                        onExited: hovered = false
                        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                        drag.target: parent
                        onPressed: (mouse) => {
                            root.draggingFromWorkspace = windowData?.workspace.id
                            root.draggingTargetSpecialWorkspace = ""
                            window.pressed = true
                            window.Drag.active = true
                            window.Drag.source = window
                            window.Drag.hotSpot.x = mouse.x
                            window.Drag.hotSpot.y = mouse.y
                        }
                        onReleased: {
                            const targetWorkspace = root.draggingTargetWorkspace
                            const targetSpecialWorkspace = root.draggingTargetSpecialWorkspace
                            window.pressed = false
                            window.Drag.active = false
                            root.draggingFromWorkspace = -1
                            root.draggingTargetWorkspace = -1
                            root.draggingTargetSpecialWorkspace = ""
                            if (targetSpecialWorkspace === root.createSpecialWorkspaceTarget) {
                                const createdName = OverviewWorkspaceMath.nextSpecialWorkspaceName(specialWorkspaces.visibleSpecialWorkspaces)
                                Hyprland.dispatch(`movetoworkspacesilent special:${createdName}, address:${window.windowData?.address}`)
                                updateWindowPosition.restart()
                            }
                            else if (targetSpecialWorkspace && targetSpecialWorkspace !== specialWorkspaces.specialWorkspaceName(windowData)) {
                                Hyprland.dispatch(`movetoworkspacesilent special:${targetSpecialWorkspace}, address:${window.windowData?.address}`)
                                updateWindowPosition.restart()
                            }
                            else if (targetWorkspace !== -1 && targetWorkspace !== windowData?.workspace.id) {
                                Hyprland.dispatch(`movetoworkspacesilent ${targetWorkspace}, address:${window.windowData?.address}`)
                                updateWindowPosition.restart()
                            }
                            else {
                                window.x = window.initX
                                window.y = window.initY
                            }
                        }
                        onClicked: (event) => {
                            if (!windowData) return;

                            if (event.button === Qt.LeftButton) {
                                GlobalStates.overviewOpen = false
                                Hyprland.dispatch(`focuswindow address:${windowData.address}`)
                                event.accepted = true
                            } else if (event.button === Qt.MiddleButton) {
                                Hyprland.dispatch(`closewindow address:${windowData.address}`)
                                event.accepted = true
                            }
                        }

                        StyledToolTip {
                            extraVisibleCondition: false
                            alternativeVisibleCondition: dragArea.containsMouse && !window.Drag.active
                            text: `${windowData?.title ?? "Unknown"}\n[${windowData?.class ?? "unknown"}] ${windowData?.xwayland ? "[XWayland] " : ""}`
                        }
                    }
                }
            }

            Rectangle { // Focused workspace indicator
                id: focusedWorkspaceIndicator
                property int activeWorkspaceRowIndex: OverviewWorkspaceMath.workspaceRow(root.effectiveActiveWorkspaceId, root.workspaceLayout)
                property int activeWorkspaceColIndex: OverviewWorkspaceMath.workspaceColumn(root.effectiveActiveWorkspaceId, root.workspaceLayout)
                x: (root.workspaceImplicitWidth + workspaceSpacing) * activeWorkspaceColIndex
                y: (root.workspaceImplicitHeight + workspaceSpacing) * activeWorkspaceRowIndex
                z: root.windowZ
                width: root.workspaceImplicitWidth
                height: root.workspaceImplicitHeight
                color: "transparent"
                radius: Appearance.rounding.screenRounding * root.scale
                border.width: 2
                border.color: root.activeBorderColor
                Behavior on x {
                    animation: Appearance.animation.elementMoveFast.numberAnimation.createObject(this)
                }
                Behavior on y {
                    animation: Appearance.animation.elementMoveFast.numberAnimation.createObject(this)
                }
            }
        }

        Item {
            id: specialWindowDragLayer
            anchors.fill: parent
            z: root.windowDraggingZ + 1
        }
    }
}
