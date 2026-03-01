pragma Singleton

import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: launcherThemesServiceRoot

    readonly property string themesBasePath: `${Quickshell.env("HOME")}/.config/hypr-theme`
    readonly property string currentThemeNamePath: `${themesBasePath}/current/theme.name`
    readonly property string currentThemeName: currentThemeNameFile.loaded ? currentThemeNameFile.text().trim() : ""
    property list<var> availableThemes: []

    function search(queryText: string): list<var> {
        let lowerQuery = queryText.toLowerCase();
        return availableThemes.filter(theme => theme.name.toLowerCase().includes(lowerQuery));
    }

    function applyTheme(themeName: string): void {
        applyThemeProcess.command = ["bash", "-c", `setsid hypr-theme-set '${themeName}' &`];
        applyThemeProcess.running = true;
    }

    function parseColorsToml(tomlText: string): var {
        let result = {};
        let lines = tomlText.split("\n");
        for (let i = 0; i < lines.length; i++) {
            let line = lines[i].trim();
            if (line.length === 0 || line.startsWith("#"))
                continue;
            let equalsIndex = line.indexOf("=");
            if (equalsIndex < 0)
                continue;
            let key = line.substring(0, equalsIndex).trim();
            let value = line.substring(equalsIndex + 1).trim().replace(/^"/, "").replace(/"$/, "");
            result[key] = value;
        }
        return result;
    }

    FileView {
        id: currentThemeNameFile
        path: Qt.url(`file://${launcherThemesServiceRoot.currentThemeNamePath}`)
        watchChanges: true
        blockLoading: true
        onFileChanged: this.reload()
    }

    Process {
        id: listThemesProcess
        command: ["bash", "-c", `
            for dir in "$HOME/.config/hypr-theme/user-themes"/* "$HOME/.config/hypr/themes"/*; do
                [ -d "$dir" ] || continue
                name=$(basename "$dir")
                colors_file="$dir/colors.toml"
                [ -f "$colors_file" ] || continue
                echo "THEME:$name"
                cat "$colors_file"
                echo "END_THEME"
            done
        `]
        running: true

        stdout: SplitParser {
            onRead: data => {
                listThemesProcess.stdoutBuffer += data + "\n";
            }
        }

        property string stdoutBuffer: ""

        onRunningChanged: {
            if (!running && stdoutBuffer.length > 0) {
                launcherThemesServiceRoot.parseThemeListOutput(stdoutBuffer);
                stdoutBuffer = "";
            }
        }
    }

    function parseThemeListOutput(output: string): void {
        let themes = [];
        let lines = output.split("\n");
        let currentName = "";
        let tomlBuffer = "";
        let inTheme = false;

        for (let i = 0; i < lines.length; i++) {
            let line = lines[i];
            if (line.startsWith("THEME:")) {
                currentName = line.substring(6);
                tomlBuffer = "";
                inTheme = true;
            } else if (line === "END_THEME" && inTheme) {
                let colors = parseColorsToml(tomlBuffer);
                if (colors.background && colors.accent) {
                    themes.push({
                        name: currentName,
                        background: colors.background,
                        foreground: colors.foreground || "#ffffff",
                        accent: colors.accent,
                        secondary: colors.color5 || colors.accent
                    });
                }
                inTheme = false;
            } else if (inTheme) {
                tomlBuffer += line + "\n";
            }
        }

        themes.sort((themeA, themeB) => themeA.name.localeCompare(themeB.name));
        availableThemes = themes;
    }

    Process {
        id: applyThemeProcess
        running: false
    }

    function reloadThemeList(): void {
        listThemesProcess.stdoutBuffer = "";
        listThemesProcess.running = true;
    }
}
