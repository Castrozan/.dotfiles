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
        command: ["find", "-L",
            `${Quickshell.env("HOME")}/.config/hypr-theme/user-themes`,
            `${Quickshell.env("HOME")}/.config/hypr/themes`,
            "-path", "*/backgrounds/*",
            "-type", "f",
            "(", "-iname", "*.jpg",
            "-o", "-iname", "*.jpeg",
            "-o", "-iname", "*.png",
            "-o", "-iname", "*.webp", ")"]
        running: true

        property var wallpaperBuffer: []

        stdout: SplitParser {
            onRead: data => {
                let trimmedPath = data.trim();
                if (trimmedPath.length === 0)
                    return;
                let lastSlashIndex = trimmedPath.lastIndexOf("/");
                let fileName = lastSlashIndex >= 0 ? trimmedPath.substring(lastSlashIndex + 1) : trimmedPath;
                listWallpapersProcess.wallpaperBuffer.push({
                    name: fileName,
                    path: trimmedPath
                });
            }
        }

        onRunningChanged: {
            if (!running && wallpaperBuffer.length > 0) {
                wallpaperBuffer.sort((wallpaperA, wallpaperB) => wallpaperA.name.localeCompare(wallpaperB.name));
                launcherWallpapersServiceRoot.availableWallpapers = wallpaperBuffer;
                wallpaperBuffer = [];
            }
        }
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
        listWallpapersProcess.wallpaperBuffer = [];
        listWallpapersProcess.running = true;
    }
}
