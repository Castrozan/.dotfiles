pragma ComponentBehavior: Bound

import "../dashboard/components"
import "../dashboard"
import ".."
import "."
import "items"
import "services"
import QtQuick
import Quickshell.Io

Item {
    id: launcherResultsListRoot

    enum Mode {
        Apps,
        Actions,
        Themes,
        Wallpapers
    }

    property string searchText: ""
    property int currentIndex: 0

    readonly property int currentMode: {
        if (searchText.startsWith(LauncherConfig.themePrefix))
            return LauncherResultsList.Themes;
        if (searchText.startsWith(LauncherConfig.wallpaperPrefix))
            return LauncherResultsList.Wallpapers;
        if (searchText.startsWith(LauncherConfig.actionPrefix))
            return LauncherResultsList.Actions;
        return LauncherResultsList.Apps;
    }

    readonly property var currentResults: {
        switch (currentMode) {
        case LauncherResultsList.Themes:
            let themeQuery = searchText.substring(LauncherConfig.themePrefix.length);
            return themeQuery.length > 0 ? LauncherThemesService.search(themeQuery) : LauncherThemesService.availableThemes;
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

    function _quoteShellArgument(commandArgument: string): string {
        return `'${commandArgument.replace(/'/g, `'\"'\"'`)}'`;
    }

    function _joinShellArguments(commandArguments: list<string>): string {
        return commandArguments.map(commandArgument => _quoteShellArgument(commandArgument)).join(" ");
    }

    function _buildDesktopEntryDetachedLaunchCommand(desktopEntry: var): string {
        let desktopEntryCommand = desktopEntry.command.length > 0
            ? _joinShellArguments(desktopEntry.command)
            : desktopEntry.execString;

        if (desktopEntry.runInTerminal) {
            let terminalCommand = ["wezterm", "start"];

            if (desktopEntry.workingDirectory.length > 0) {
                terminalCommand.push("--cwd");
                terminalCommand.push(desktopEntry.workingDirectory);
            }

            terminalCommand.push("--");

            if (desktopEntry.command.length > 0) {
                terminalCommand = terminalCommand.concat(desktopEntry.command);
            } else {
                terminalCommand.push("sh");
                terminalCommand.push("-lc");
                terminalCommand.push(desktopEntry.execString);
            }

            return _joinShellArguments(terminalCommand);
        }

        if (desktopEntry.workingDirectory.length > 0) {
            return `cd ${_quoteShellArgument(desktopEntry.workingDirectory)} && ${desktopEntryCommand}`;
        }

        return desktopEntryCommand;
    }

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
            _runDetachedCommand(_buildDesktopEntryDetachedLaunchCommand(item));
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
        case LauncherResultsList.Themes:
            LauncherThemesService.applyTheme(item.name);
            itemActivated();
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

    implicitHeight: currentMode === LauncherResultsList.Wallpapers
        ? Math.max(wallpapersListView.implicitHeight, LauncherConfig.itemHeight)
        : Math.max(verticalListView.implicitHeight, LauncherConfig.itemHeight)

    ListView {
        id: verticalListView

        anchors.fill: parent
        visible: launcherResultsListRoot.currentMode !== LauncherResultsList.Wallpapers

        model: launcherResultsListRoot.currentResults
        clip: true
        spacing: Appearance.spacing.smaller

        implicitHeight: Math.min(
            launcherResultsListRoot.visibleItemCount * (LauncherConfig.itemHeight + spacing),
            LauncherConfig.maxVisibleItems * (LauncherConfig.itemHeight + spacing)
        )

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
                case LauncherResultsList.Themes:
                    return themeItemComponent;
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

            Component {
                id: themeItemComponent
                LauncherThemeItem {
                    themeData: delegateLoader.modelData
                    isCurrentTheme: delegateLoader.modelData.name === LauncherThemesService.currentThemeName
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
