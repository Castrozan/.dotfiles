pragma Singleton

import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: launcherWallpapersServiceRoot

    readonly property string themesBasePath: `${Quickshell.env("HOME")}/.config/hypr-theme`
    readonly property string currentBackgroundLink: `${themesBasePath}/current/background`
    property string currentWallpaperPath: ""
    property list<var> availableWallpapers: []

    function search(queryText: string): list<var> {
        let lowerQuery = queryText.toLowerCase();
        return availableWallpapers.filter(wallpaper => wallpaper.name.toLowerCase().includes(lowerQuery));
    }

    function setWallpaper(wallpaperPath: string): void {
        symlinkWallpaperProcess.command = ["ln", "-sf", wallpaperPath, currentBackgroundLink];
        symlinkWallpaperProcess.running = true;
    }

    Process {
        id: readCurrentWallpaperProcess
        command: ["readlink", "-f", `${launcherWallpapersServiceRoot.currentBackgroundLink}`]
        running: true

        stdout: SplitParser {
            onRead: data => {
                launcherWallpapersServiceRoot.currentWallpaperPath = data.trim();
            }
        }
    }

    Process {
        id: listWallpapersProcess
        command: ["bash", "-c", "find -L \"$HOME/.config/hypr-theme/user-themes\" \"$HOME/.config/hypr/themes\" -path '*/backgrounds/*' -type f \\( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' \\)"]
        running: true

        property string stdoutBuffer: ""

        stdout: SplitParser {
            onRead: data => {
                listWallpapersProcess.stdoutBuffer += data + "\n";
            }
        }

        onRunningChanged: {
            if (!running && stdoutBuffer.length > 0) {
                launcherWallpapersServiceRoot.parseWallpaperListOutput(stdoutBuffer);
                stdoutBuffer = "";
            }
        }
    }

    function parseWallpaperListOutput(output: string): void {
        let wallpapers = [];
        let lines = output.split("\n");
        for (let i = 0; i < lines.length; i++) {
            let trimmedPath = lines[i].trim();
            if (trimmedPath.length === 0)
                continue;
            let lastSlashIndex = trimmedPath.lastIndexOf("/");
            let fileName = lastSlashIndex >= 0 ? trimmedPath.substring(lastSlashIndex + 1) : trimmedPath;
            wallpapers.push({
                name: fileName,
                path: trimmedPath
            });
        }
        wallpapers.sort((wallpaperA, wallpaperB) => wallpaperA.name.localeCompare(wallpaperB.name));
        availableWallpapers = wallpapers;
    }

    Process {
        id: symlinkWallpaperProcess
        running: false
        onRunningChanged: {
            if (!running) {
                applyWallpaperProcess.running = true;
            }
        }
    }

    Process {
        id: applyWallpaperProcess
        command: ["hypr-theme-bg-apply"]
        running: false
        onRunningChanged: {
            if (!running) {
                readCurrentWallpaperProcess.running = true;
            }
        }
    }

    function reloadWallpaperList(): void {
        availableWallpapers = [];
        listWallpapersProcess.stdoutBuffer = "";
        listWallpapersProcess.running = true;
    }
}
