import QtQuick

Item {
    id: drawerHoverControllerRoot

    required property var drawerState

    property bool pointerOverBar: false
    property int barAutoHideInterval: 6000
    property int activeWorkspaceId: 0
    property int previousWorkspaceId: 0

    onActiveWorkspaceIdChanged: {
        if (activeWorkspaceId === 0)
            return;
        const workspaceChanged = previousWorkspaceId !== 0 && previousWorkspaceId !== activeWorkspaceId;
        previousWorkspaceId = activeWorkspaceId;
        if (workspaceChanged)
            showBarTemporarily();
    }

    readonly property alias bar: barHoverTiming
    readonly property alias dashboard: dashboardHoverTiming
    readonly property alias launcher: launcherHoverTiming
    readonly property alias session: sessionHoverTiming
    readonly property alias utilities: utilitiesHoverTiming
    readonly property alias sidebar: sidebarHoverTiming
    readonly property alias osd: osdHoverTiming

    function toggleBarTemporarily(): void {
        barAutoHideTimer.stop();
        barHoverTiming.cancelPendingTransition();
        if (drawerHoverControllerRoot.drawerState.barVisible) {
            drawerHoverControllerRoot.drawerState.clearPopout();
            drawerHoverControllerRoot.drawerState.closeBar();
            return;
        }
        drawerHoverControllerRoot.showBarTemporarily();
    }

    function showBarTemporarily(): void {
        barHoverTiming.cancelPendingTransition();
        drawerHoverControllerRoot.drawerState.openBar();
        barAutoHideTimer.restart();
    }

    function showOsdTemporarily(): void {
        drawerHoverControllerRoot.drawerState.openOsd();
        osdAutoHideTimer.restart();
    }

    function popoutContentEntered(): void {
        drawerHoverControllerRoot.drawerState.setPopoutHovered(true);
        popoutHideTimer.stop();
    }

    function popoutContentLeft(): void {
        drawerHoverControllerRoot.drawerState.setPopoutHovered(false);
        popoutHideTimer.restart();
    }

    DrawerHoverTiming {
        id: barHoverTiming

        contentHovered: drawerHoverControllerRoot.drawerState.barHovered || drawerHoverControllerRoot.drawerState.hasActivePopout
        onContentPointerEntered: drawerHoverControllerRoot.drawerState.setBarHovered(true)
        onContentPointerLeft: drawerHoverControllerRoot.drawerState.setBarHovered(false)
        onRevealRequested: drawerHoverControllerRoot.drawerState.openBar()
        onConcealRequested: {
            if (!barAutoHideTimer.running)
                drawerHoverControllerRoot.drawerState.closeBar();
        }
    }

    DrawerHoverTiming {
        id: dashboardHoverTiming

        contentHovered: drawerHoverControllerRoot.drawerState.dashboardHovered
        onContentPointerEntered: drawerHoverControllerRoot.drawerState.setDashboardHovered(true)
        onContentPointerLeft: drawerHoverControllerRoot.drawerState.setDashboardHovered(false)
        onRevealRequested: drawerHoverControllerRoot.drawerState.openDashboard()
        onConcealRequested: drawerHoverControllerRoot.drawerState.closeDashboard()
    }

    DrawerHoverTiming {
        id: launcherHoverTiming

        revealDelayInterval: 0
        contentHovered: drawerHoverControllerRoot.drawerState.launcherHovered
        onContentPointerEntered: drawerHoverControllerRoot.drawerState.setLauncherHovered(true)
        onContentPointerLeft: drawerHoverControllerRoot.drawerState.setLauncherHovered(false)
        onRevealRequested: drawerHoverControllerRoot.drawerState.openLauncher()
        onConcealRequested: drawerHoverControllerRoot.drawerState.closeLauncher()
    }

    DrawerHoverTiming {
        id: sessionHoverTiming

        contentHovered: drawerHoverControllerRoot.drawerState.sessionHovered
        onContentPointerEntered: drawerHoverControllerRoot.drawerState.setSessionHovered(true)
        onContentPointerLeft: drawerHoverControllerRoot.drawerState.setSessionHovered(false)
        onRevealRequested: drawerHoverControllerRoot.drawerState.openSession()
        onConcealRequested: drawerHoverControllerRoot.drawerState.closeSession()
    }

    DrawerHoverTiming {
        id: utilitiesHoverTiming

        contentHovered: drawerHoverControllerRoot.drawerState.utilitiesHovered
        onContentPointerEntered: drawerHoverControllerRoot.drawerState.setUtilitiesHovered(true)
        onContentPointerLeft: drawerHoverControllerRoot.drawerState.setUtilitiesHovered(false)
        onConcealRequested: drawerHoverControllerRoot.drawerState.closeUtilities()
    }

    DrawerHoverTiming {
        id: sidebarHoverTiming

        contentHovered: drawerHoverControllerRoot.drawerState.sidebarHovered
        onContentPointerEntered: drawerHoverControllerRoot.drawerState.setSidebarHovered(true)
        onContentPointerLeft: drawerHoverControllerRoot.drawerState.setSidebarHovered(false)
        onRevealRequested: drawerHoverControllerRoot.drawerState.openSidebar()
        onConcealRequested: drawerHoverControllerRoot.drawerState.closeSidebar()
    }

    DrawerHoverTiming {
        id: osdHoverTiming

        contentHovered: drawerHoverControllerRoot.drawerState.osdHovered
        onContentPointerEntered: {
            drawerHoverControllerRoot.drawerState.setOsdHovered(true);
            osdAutoHideTimer.stop();
        }
        onContentPointerLeft: drawerHoverControllerRoot.drawerState.setOsdHovered(false)
        onRevealRequested: drawerHoverControllerRoot.drawerState.openOsd()
        onConcealRequested: drawerHoverControllerRoot.drawerState.closeOsd()
    }

    Timer {
        id: popoutHideTimer

        interval: 450
        onTriggered: {
            if (!drawerHoverControllerRoot.drawerState.popoutHovered && !drawerHoverControllerRoot.pointerOverBar && !drawerHoverControllerRoot.drawerState.popoutIconHovered)
                drawerHoverControllerRoot.drawerState.clearPopout();
        }
    }

    Timer {
        id: barAutoHideTimer

        interval: drawerHoverControllerRoot.barAutoHideInterval
        onTriggered: {
            if (!drawerHoverControllerRoot.drawerState.barHovered && !barHoverTiming.triggerHovered && !drawerHoverControllerRoot.drawerState.hasActivePopout)
                drawerHoverControllerRoot.drawerState.closeBar();
        }
    }

    Timer {
        id: osdAutoHideTimer

        interval: 2000
        onTriggered: drawerHoverControllerRoot.drawerState.closeOsd()
    }

    Connections {
        target: drawerHoverControllerRoot.drawerState

        function onPopoutCurrentNameChanged(): void {
            if (!drawerHoverControllerRoot.drawerState.hasActivePopout && !drawerHoverControllerRoot.drawerState.barHovered)
                barHoverTiming.contentLeft();
        }

        function onPopoutShown(): void {
            popoutHideTimer.stop();
        }

        function onPopoutHideRequested(): void {
            popoutHideTimer.restart();
        }
    }
}
