pragma ComponentBehavior: Bound

import "../dashboard/components"
import "../dashboard"
import ".."
import "."
import "items"
import "services"
import "services/DesktopEntryCommand.js" as DesktopEntryCommand
import QtQuick
import Quickshell.Io

Item {
    id: launcherResultsListRoot

    enum Mode {
        Apps,
        Actions,
        Wallpapers
    }

    property string searchText: ""
    property int currentIndex: 0

    readonly property int currentMode: {
        if (searchText.startsWith(LauncherConfig.wallpaperPrefix))
            return LauncherResultsList.Wallpapers;
        if (searchText.startsWith(LauncherConfig.actionPrefix))
            return LauncherResultsList.Actions;
        return LauncherResultsList.Apps;
    }

    readonly property var currentResults: {
        switch (currentMode) {
        case LauncherResultsList.Wallpapers:
            return wallpaperResults;
        case LauncherResultsList.Actions:
            let actionQuery = searchText.substring(LauncherConfig.actionPrefix.length).trim();
            return actionQuery.length > 0 ? LauncherActionsService.search(actionQuery) : LauncherActionsService.allActions;
        default:
            return searchText.length > 0 ? LauncherAppsService.search(searchText) : LauncherAppsService.allApplicationsSorted();
        }
    }

    readonly property int visibleItemCount: Math.min(currentResults.length, LauncherConfig.maxVisibleItems)

    signal itemActivated
    signal autoCompleteRequested(string text)

    function _runDetachedCommand(detachedCommand: string): void {
        executeDetachedCommandProcess.command = ["hyprctl", "dispatch", "exec", detachedCommand];
        executeDetachedCommandProcess.running = true;
    }

    function activateCurrentItem(): void {
        if (currentResults.length === 0)
            return;

        let safeIndex = Math.min(currentIndex, currentResults.length - 1);
        let item = currentResults[safeIndex];

        switch (currentMode) {
        case LauncherResultsList.Apps:
            LauncherAppsService.recordAppLaunch(item);
            _runDetachedCommand(DesktopEntryCommand.detachedLaunchCommand(item));
            itemActivated();
            break;
        case LauncherResultsList.Actions:
            if (item.autoCompleteText) {
                autoCompleteRequested(item.autoCompleteText);
            } else if (item.command) {
                _runDetachedCommand(item.command);
                itemActivated();
            }
            break;
        case LauncherResultsList.Wallpapers:
            LauncherWallpapersService.setWallpaper(item.path);
            itemActivated();
            break;
        }
    }

    function moveSelectionUp(): void {
        if (currentIndex > 0)
            currentIndex--;
    }

    function moveSelectionDown(): void {
        if (currentIndex < currentResults.length - 1)
            currentIndex++;
    }

    onSearchTextChanged: currentIndex = 0

    readonly property var wallpaperResults: {
        if (currentMode !== LauncherResultsList.Wallpapers)
            return [];
        let wallpaperQuery = searchText.substring(LauncherConfig.wallpaperPrefix.length);
        return wallpaperQuery.length > 0 ? LauncherWallpapersService.search(wallpaperQuery) : LauncherWallpapersService.availableWallpapers;
    }

    implicitHeight: currentMode === LauncherResultsList.Wallpapers ? Math.max(wallpapersListView.implicitHeight, LauncherConfig.itemHeight) : Math.max(verticalListView.implicitHeight, LauncherConfig.itemHeight)

    ListView {
        id: verticalListView

        anchors.fill: parent
        visible: launcherResultsListRoot.currentMode !== LauncherResultsList.Wallpapers

        model: launcherResultsListRoot.currentResults
        clip: true
        spacing: Appearance.spacing.smaller

        implicitHeight: Math.min(launcherResultsListRoot.visibleItemCount * (LauncherConfig.itemHeight + spacing), LauncherConfig.maxVisibleItems * (LauncherConfig.itemHeight + spacing))

        currentIndex: launcherResultsListRoot.currentIndex

        delegate: Loader {
            id: delegateLoader

            required property var modelData
            required property int index

            width: verticalListView.width
            height: LauncherConfig.itemHeight

            sourceComponent: {
                switch (launcherResultsListRoot.currentMode) {
                case LauncherResultsList.Actions:
                    return actionItemComponent;
                default:
                    return appItemComponent;
                }
            }

            Component {
                id: appItemComponent
                LauncherAppItem {
                    desktopEntry: delegateLoader.modelData
                    isCurrentItem: delegateLoader.index === launcherResultsListRoot.currentIndex
                    onActivated: launcherResultsListRoot.activateCurrentItem()
                }
            }

            Component {
                id: actionItemComponent
                LauncherActionItem {
                    actionData: delegateLoader.modelData
                    isCurrentItem: delegateLoader.index === launcherResultsListRoot.currentIndex
                    onActivated: {
                        launcherResultsListRoot.currentIndex = delegateLoader.index;
                        launcherResultsListRoot.activateCurrentItem();
                    }
                }
            }
        }
    }

    ListView {
        id: wallpapersListView

        anchors.fill: parent
        visible: launcherResultsListRoot.currentMode === LauncherResultsList.Wallpapers

        orientation: ListView.Horizontal
        spacing: Appearance.spacing.small
        clip: true

        implicitHeight: LauncherConfig.wallpaperThumbnailSize

        model: launcherResultsListRoot.wallpaperResults
        currentIndex: launcherResultsListRoot.currentIndex

        delegate: LauncherWallpaperItem {
            required property var modelData
            required property int index

            height: wallpapersListView.height

            wallpaperData: modelData
            isCurrentWallpaper: modelData.path === LauncherWallpapersService.currentWallpaperPath
            isCurrentItem: index === launcherResultsListRoot.currentIndex
            onActivated: {
                launcherResultsListRoot.currentIndex = index;
                launcherResultsListRoot.activateCurrentItem();
            }
        }
    }

    Process {
        id: executeDetachedCommandProcess
        running: false
    }
}
