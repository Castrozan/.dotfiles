import QtQuick

QtObject {
    id: drawerStateRoot

    required property var popoutAnchorResolver

    property string popoutCurrentName: ""
    property real popoutCenterY: 0
    property bool popoutHovered: false
    property bool popoutIconHovered: false
    property bool dashboardVisible: false
    property bool dashboardHovered: false
    property bool launcherVisible: false
    property bool launcherHovered: false
    property bool sessionVisible: false
    property bool sessionHovered: false
    property bool utilitiesVisible: false
    property bool utilitiesHovered: false
    property bool sidebarVisible: false
    property bool sidebarHovered: false
    property bool osdVisible: false
    property bool osdHovered: false

    readonly property bool hasActivePopout: drawerStateRoot.popoutCurrentName !== ""
    readonly property bool hasAnyPanelVisible: drawerStateRoot.dashboardVisible || drawerStateRoot.launcherVisible || drawerStateRoot.sessionVisible || drawerStateRoot.utilitiesVisible || drawerStateRoot.sidebarVisible

    signal popoutShown()
    signal popoutHideRequested()

    function showPopout(name: string, centerY: real): void {
        drawerStateRoot.popoutCurrentName = name;
        drawerStateRoot.popoutCenterY = centerY;
        drawerStateRoot.popoutShown();
    }

    function showPopoutByName(name: string): void {
        drawerStateRoot.showPopout(name, drawerStateRoot.popoutAnchorResolver.centerYForPopout(name));
    }

    function togglePopout(name: string): void {
        if (drawerStateRoot.popoutCurrentName === name) {
            drawerStateRoot.clearPopout();
            return;
        }
        drawerStateRoot.showPopoutByName(name);
    }

    function hidePopout(): void {
        if (!drawerStateRoot.popoutHovered && !drawerStateRoot.popoutIconHovered)
            drawerStateRoot.popoutHideRequested();
    }

    function clearPopout(): void {
        drawerStateRoot.popoutCurrentName = "";
    }

    function setPopoutHovered(hovered: bool): void {
        drawerStateRoot.popoutHovered = hovered;
    }

    function toggleDashboard(): void {
        drawerStateRoot.dashboardVisible = !drawerStateRoot.dashboardVisible;
    }

    function openDashboard(): void {
        drawerStateRoot.dashboardVisible = true;
    }

    function closeDashboard(): void {
        drawerStateRoot.dashboardVisible = false;
    }

    function setDashboardHovered(hovered: bool): void {
        drawerStateRoot.dashboardHovered = hovered;
    }

    function toggleLauncher(): void {
        drawerStateRoot.launcherVisible = !drawerStateRoot.launcherVisible;
    }

    function openLauncher(): void {
        drawerStateRoot.launcherVisible = true;
    }

    function closeLauncher(): void {
        drawerStateRoot.launcherVisible = false;
    }

    function setLauncherHovered(hovered: bool): void {
        drawerStateRoot.launcherHovered = hovered;
    }

    function toggleSession(): void {
        drawerStateRoot.sessionVisible = !drawerStateRoot.sessionVisible;
    }

    function openSession(): void {
        drawerStateRoot.sessionVisible = true;
    }

    function closeSession(): void {
        drawerStateRoot.sessionVisible = false;
    }

    function setSessionHovered(hovered: bool): void {
        drawerStateRoot.sessionHovered = hovered;
    }

    function toggleUtilities(): void {
        drawerStateRoot.utilitiesVisible = !drawerStateRoot.utilitiesVisible;
    }

    function closeUtilities(): void {
        drawerStateRoot.utilitiesVisible = false;
    }

    function setUtilitiesHovered(hovered: bool): void {
        drawerStateRoot.utilitiesHovered = hovered;
    }

    function toggleSidebar(): void {
        drawerStateRoot.sidebarVisible = !drawerStateRoot.sidebarVisible;
    }

    function openSidebar(): void {
        drawerStateRoot.sidebarVisible = true;
    }

    function closeSidebar(): void {
        drawerStateRoot.sidebarVisible = false;
    }

    function setSidebarHovered(hovered: bool): void {
        drawerStateRoot.sidebarHovered = hovered;
    }

    function openOsd(): void {
        drawerStateRoot.osdVisible = true;
    }

    function closeOsd(): void {
        drawerStateRoot.osdVisible = false;
    }

    function setOsdHovered(hovered: bool): void {
        drawerStateRoot.osdHovered = hovered;
    }

    function closeAllPanels(): void {
        drawerStateRoot.closeDashboard();
        drawerStateRoot.closeLauncher();
        drawerStateRoot.closeSession();
        drawerStateRoot.closeUtilities();
        drawerStateRoot.closeSidebar();
    }
}
