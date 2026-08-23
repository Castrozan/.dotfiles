pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import "functions"
import "." as Common

Singleton {
    id: root
    property string colorSource: Common.Config.options.appearance.colorSource
    property string caelestiaAccentProfile: Common.Config.options.appearance.caelestia.accentProfile
    property string lastCaelestiaPayload: ""
    property QtObject m3colors: {
        if (colorSource === "matugen" && matugenLoader.item)
            return matugenLoader.item;
        if (colorSource === "caelestia" && caelestiaPaletteLoaded)
            return caelestiaColors;
        if (hyprThemeLoaded)
            return hyprThemeColors;
        return defaultColors;
    }
    property AppearanceAnimation animation
    property AppearanceAnimationCurves animationCurves
    property AppearanceColors colors
    property AppearanceRounding rounding
    property AppearanceFont font
    property AppearanceSizes sizes
    property bool caelestiaPaletteLoaded: false
    property bool hyprThemeLoaded: false

    Loader {
        id: matugenLoader
        active: root.colorSource === "matugen"
        source: "Appearance.colors.qml"
    }

    FileView {
        id: hyprThemeFile
        path: Qt.url(`file://${Quickshell.env("HOME")}/.config/hypr-theme/current/theme/quickshell-bar-colors.json`)
        watchChanges: true
        blockLoading: true
        onFileChanged: this.reload()
        onLoadedChanged: {
            if (!loaded) return;
            root.applyHyprTheme();
        }
    }

    function applyHyprTheme() {
        if (!hyprThemeFile.loaded) return;
        try {
            const theme = JSON.parse(hyprThemeFile.text());
            const bg = theme.background ?? "#161217";
            const fg = theme.foreground ?? "#EAE0E7";
            const primary = theme.primary ?? "#89b4fa";
            const accent = theme.accent ?? "#94e2d5";
            const dim = theme.dim ?? "#6c7086";
            const surface = theme.surface ?? "#45475a";

            hyprThemeColors.m3primary = primary;
            hyprThemeColors.m3onPrimary = relativeLuminance(primary) > 0.5 ? "#121212" : "#f5f5f5";
            hyprThemeColors.m3primaryContainer = ColorUtils.mix(primary, bg, 0.3);
            hyprThemeColors.m3onPrimaryContainer = fg;
            hyprThemeColors.m3secondary = accent;
            hyprThemeColors.m3onSecondary = relativeLuminance(accent) > 0.5 ? "#121212" : "#f5f5f5";
            hyprThemeColors.m3secondaryContainer = ColorUtils.mix(accent, bg, 0.25);
            hyprThemeColors.m3onSecondaryContainer = fg;
            // Panel bg is lighter, workspace tiles are darker (matches reference layout)
            hyprThemeColors.m3background = ColorUtils.mix(bg, fg, 0.72);
            hyprThemeColors.m3onBackground = fg;
            hyprThemeColors.m3surface = ColorUtils.mix(bg, fg, 0.72);
            hyprThemeColors.m3surfaceContainerLow = ColorUtils.mix(bg, fg, 0.92);
            hyprThemeColors.m3surfaceContainer = ColorUtils.mix(bg, fg, 0.82);
            hyprThemeColors.m3surfaceContainerHigh = ColorUtils.mix(bg, fg, 0.75);
            hyprThemeColors.m3surfaceContainerHighest = ColorUtils.mix(bg, fg, 0.68);
            hyprThemeColors.m3onSurface = fg;
            hyprThemeColors.m3surfaceVariant = ColorUtils.mix(dim, fg, 0.6);
            hyprThemeColors.m3onSurfaceVariant = ColorUtils.mix(fg, bg, 0.15);
            hyprThemeColors.m3inverseSurface = fg;
            hyprThemeColors.m3inverseOnSurface = bg;
            hyprThemeColors.m3outline = ColorUtils.mix(dim, fg, 0.6);
            hyprThemeColors.m3outlineVariant = ColorUtils.mix(dim, bg, 0.3);
            hyprThemeColors.m3shadow = "#000000";
            hyprThemeColors.darkmode = relativeLuminance(bg) < 0.5;

            root.hyprThemeLoaded = true;
        } catch (e) {
            console.warn("overview: failed to parse hypr-theme colors", e);
        }
    }

    property MaterialColorScheme hyprThemeColors: MaterialColorScheme {
        darkmode: true
        m3primary: root.defaultColors.m3primary
        m3onPrimary: root.defaultColors.m3onPrimary
        m3primaryContainer: root.defaultColors.m3primaryContainer
        m3onPrimaryContainer: root.defaultColors.m3onPrimaryContainer
        m3secondary: root.defaultColors.m3secondary
        m3onSecondary: root.defaultColors.m3onSecondary
        m3secondaryContainer: root.defaultColors.m3secondaryContainer
        m3onSecondaryContainer: root.defaultColors.m3onSecondaryContainer
        m3background: root.defaultColors.m3background
        m3onBackground: root.defaultColors.m3onBackground
        m3surface: root.defaultColors.m3surface
        m3surfaceContainerLow: root.defaultColors.m3surfaceContainerLow
        m3surfaceContainer: root.defaultColors.m3surfaceContainer
        m3surfaceContainerHigh: root.defaultColors.m3surfaceContainerHigh
        m3surfaceContainerHighest: root.defaultColors.m3surfaceContainerHighest
        m3onSurface: root.defaultColors.m3onSurface
        m3surfaceVariant: root.defaultColors.m3surfaceVariant
        m3onSurfaceVariant: root.defaultColors.m3onSurfaceVariant
        m3inverseSurface: root.defaultColors.m3inverseSurface
        m3inverseOnSurface: root.defaultColors.m3inverseOnSurface
        m3outline: root.defaultColors.m3outline
        m3outlineVariant: root.defaultColors.m3outlineVariant
        m3shadow: root.defaultColors.m3shadow
    }

    property MaterialColorScheme defaultColors: MaterialColorScheme {
        darkmode: true
        m3primary: "#E5B6F2"
        m3onPrimary: "#452152"
        m3primaryContainer: "#5D386A"
        m3onPrimaryContainer: "#F9D8FF"
        m3secondary: "#D5C0D7"
        m3onSecondary: "#392C3D"
        m3secondaryContainer: "#534457"
        m3onSecondaryContainer: "#F2DCF3"
        m3background: "#161217"
        m3onBackground: "#EAE0E7"
        m3surface: "#161217"
        m3surfaceContainerLow: "#1F1A1F"
        m3surfaceContainer: "#231E23"
        m3surfaceContainerHigh: "#2D282E"
        m3surfaceContainerHighest: "#383339"
        m3onSurface: "#EAE0E7"
        m3surfaceVariant: "#4C444D"
        m3onSurfaceVariant: "#CFC3CD"
        m3inverseSurface: "#EAE0E7"
        m3inverseOnSurface: "#342F34"
        m3outline: "#988E97"
        m3outlineVariant: "#4C444D"
        m3shadow: "#000000"
    }

    property MaterialColorScheme caelestiaColors: MaterialColorScheme {
        darkmode: root.defaultColors.darkmode
        m3primary: root.defaultColors.m3primary
        m3onPrimary: root.defaultColors.m3onPrimary
        m3primaryContainer: root.defaultColors.m3primaryContainer
        m3onPrimaryContainer: root.defaultColors.m3onPrimaryContainer
        m3secondary: root.defaultColors.m3secondary
        m3onSecondary: root.defaultColors.m3onSecondary
        m3secondaryContainer: root.defaultColors.m3secondaryContainer
        m3onSecondaryContainer: root.defaultColors.m3onSecondaryContainer
        m3background: root.defaultColors.m3background
        m3onBackground: root.defaultColors.m3onBackground
        m3surface: root.defaultColors.m3surface
        m3surfaceContainerLow: root.defaultColors.m3surfaceContainerLow
        m3surfaceContainer: root.defaultColors.m3surfaceContainer
        m3surfaceContainerHigh: root.defaultColors.m3surfaceContainerHigh
        m3surfaceContainerHighest: root.defaultColors.m3surfaceContainerHighest
        m3onSurface: root.defaultColors.m3onSurface
        m3surfaceVariant: root.defaultColors.m3surfaceVariant
        m3onSurfaceVariant: root.defaultColors.m3onSurfaceVariant
        m3inverseSurface: root.defaultColors.m3inverseSurface
        m3inverseOnSurface: root.defaultColors.m3inverseOnSurface
        m3outline: root.defaultColors.m3outline
        m3outlineVariant: root.defaultColors.m3outlineVariant
        m3shadow: root.defaultColors.m3shadow
    }

    function loadCaelestiaPalette() {
        getCaelestiaScheme.running = true;
    }

    function relativeLuminance(color) {
        const c = Qt.color(color);
        function channel(v) {
            return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
        }
        return (0.2126 * channel(c.r)) + (0.7152 * channel(c.g)) + (0.0722 * channel(c.b));
    }

    function bestOnColor(backgroundColor) {
        return relativeLuminance(backgroundColor) > 0.5 ? "#121212" : "#f5f5f5";
    }

    function firstColor(palette, keys, fallback) {
        for (const key of keys) {
            if (palette[key])
                return palette[key];
        }
        return fallback;
    }

    function applyCaelestiaPalette(palette, mode) {
        if (caelestiaAccentProfile === "vibrant") {
            const primary = firstColor(palette, ["blue", "klink", "term12", "primary"], defaultColors.m3primary);
            const secondary = firstColor(palette, ["mauve", "lavender", "term13", "secondary"], defaultColors.m3secondary);
            const tertiary = firstColor(palette, ["pink", "rosewater", "term11", "tertiary"], defaultColors.m3secondaryContainer);
            const primaryContainer = firstColor(palette, ["sapphire", "klinkSelection", "primaryContainer"], defaultColors.m3primaryContainer);
            const secondaryContainer = firstColor(palette, ["surface2", "secondaryContainer"], defaultColors.m3secondaryContainer);

            caelestiaColors.m3primary = primary;
            caelestiaColors.m3onPrimary = bestOnColor(primary);
            caelestiaColors.m3primaryContainer = primaryContainer;
            caelestiaColors.m3onPrimaryContainer = bestOnColor(primaryContainer);
            caelestiaColors.m3secondary = secondary;
            caelestiaColors.m3onSecondary = bestOnColor(secondary);
            caelestiaColors.m3secondaryContainer = secondaryContainer;
            caelestiaColors.m3onSecondaryContainer = bestOnColor(secondaryContainer);
            // Preserve a stronger accent presence across UI mixes.
            caelestiaColors.m3surfaceVariant = firstColor(palette, ["surface1", "surfaceVariant"], defaultColors.m3surfaceVariant);
            caelestiaColors.m3outline = firstColor(palette, ["overlay2", "outline"], defaultColors.m3outline);
            caelestiaColors.m3outlineVariant = firstColor(palette, ["overlay0", "outlineVariant"], defaultColors.m3outlineVariant);
            if (tertiary)
                caelestiaColors.m3secondaryContainer = ColorUtils.mix(secondaryContainer, tertiary, 0.7);
        } else {
            const map = {
                "primary": "m3primary",
                "onPrimary": "m3onPrimary",
                "primaryContainer": "m3primaryContainer",
                "onPrimaryContainer": "m3onPrimaryContainer",
                "secondary": "m3secondary",
                "onSecondary": "m3onSecondary",
                "secondaryContainer": "m3secondaryContainer",
                "onSecondaryContainer": "m3onSecondaryContainer",
                "surfaceVariant": "m3surfaceVariant",
                "outline": "m3outline",
                "outlineVariant": "m3outlineVariant"
            };
            for (const key in map) {
                if (palette[key])
                    caelestiaColors[map[key]] = palette[key];
            }
        }

        // Keep foundational tones from Material keys for readability.
        const baseMap = {
            "background": "m3background",
            "onBackground": "m3onBackground",
            "surface": "m3surface",
            "surfaceContainerLow": "m3surfaceContainerLow",
            "surfaceContainer": "m3surfaceContainer",
            "surfaceContainerHigh": "m3surfaceContainerHigh",
            "surfaceContainerHighest": "m3surfaceContainerHighest",
            "onSurface": "m3onSurface",
            "inverseSurface": "m3inverseSurface",
            "inverseOnSurface": "m3inverseOnSurface",
            "shadow": "m3shadow"
        };
        for (const key in baseMap) {
            if (palette[key])
                caelestiaColors[baseMap[key]] = palette[key];
        }

        if (palette["onSurfaceVariant"])
            caelestiaColors.m3onSurfaceVariant = palette["onSurfaceVariant"];

        if (mode === "light")
            caelestiaColors.darkmode = false;
        else if (mode === "dark")
            caelestiaColors.darkmode = true;
    }

    Process {
        id: getCaelestiaScheme
        command: ["sh", "-lc", "caelestia scheme get 2>/dev/null || true"]
        stdout: StdioCollector {
            id: caelestiaCollector
            onStreamFinished: {
                const text = caelestiaCollector.text;
                if (!text || !text.trim()) {
                    root.caelestiaPaletteLoaded = false;
                    return;
                }

                const ansiPattern = /\x1b\[[0-9;]*m/g;
                const lines = text.split("\n");
                let mode = "";
                const palette = ({});

                for (const rawLine of lines) {
                    const line = rawLine.replace(ansiPattern, "").trim();

                    if (line.startsWith("Mode:")) {
                        mode = line.split(":")[1]?.trim()?.toLowerCase() ?? "";
                        continue;
                    }

                    const match = line.match(/^([A-Za-z0-9_]+):\s*.*?([0-9a-fA-F]{6})$/);
                    if (!match)
                        continue;

                    palette[match[1]] = `#${match[2]}`;
                }

                const normalized = JSON.stringify({ mode: mode, palette: palette, profile: caelestiaAccentProfile });
                if (normalized === root.lastCaelestiaPayload)
                    return;

                root.lastCaelestiaPayload = normalized;
                applyCaelestiaPalette(palette, mode);
                root.caelestiaPaletteLoaded = Object.keys(palette).length > 0;
            }
        }
    }

    Timer {
        id: caelestiaRefreshTimer
        interval: Math.max(500, Common.Config.options.appearance.caelestia.refreshInterval)
        running: root.colorSource === "caelestia" && Common.Config.options.appearance.caelestia.autoRefresh
        repeat: true
        triggeredOnStart: false
        onTriggered: root.loadCaelestiaPalette()
    }

    onColorSourceChanged: {
        if (colorSource === "caelestia")
            loadCaelestiaPalette();
    }

    onCaelestiaAccentProfileChanged: {
        if (colorSource === "caelestia") {
            root.lastCaelestiaPayload = "";
            loadCaelestiaPalette();
        }
    }

    Component.onCompleted: {
        if (colorSource === "caelestia")
            loadCaelestiaPalette();
    }

    colors: AppearanceColors {
        id: appearanceColors
        colSubtext: root.m3colors.m3outline
        colLayer0: root.m3colors.m3background
        colOnLayer0: root.m3colors.m3onBackground
        colLayer0Border: ColorUtils.mix(root.m3colors.m3outlineVariant, appearanceColors.colLayer0, 0.4)
        colLayer1: root.m3colors.m3surfaceContainerLow
        colOnLayer1: root.m3colors.m3onSurfaceVariant
        colOnLayer1Inactive: ColorUtils.mix(appearanceColors.colOnLayer1, appearanceColors.colLayer1, 0.45)
        colLayer1Hover: ColorUtils.mix(appearanceColors.colLayer1, appearanceColors.colOnLayer1, 0.92)
        colLayer1Active: ColorUtils.mix(appearanceColors.colLayer1, appearanceColors.colOnLayer1, 0.85)
        colLayer2: root.m3colors.m3surfaceContainer
        colOnLayer2: root.m3colors.m3onSurface
        colLayer2Hover: ColorUtils.mix(appearanceColors.colLayer2, appearanceColors.colOnLayer2, 0.90)
        colLayer2Active: ColorUtils.mix(appearanceColors.colLayer2, appearanceColors.colOnLayer2, 0.80)
        colPrimary: root.m3colors.m3primary
        colOnPrimary: root.m3colors.m3onPrimary
        colSecondary: root.m3colors.m3secondary
        colSecondaryContainer: root.m3colors.m3secondaryContainer
        colOnSecondaryContainer: root.m3colors.m3onSecondaryContainer
        colTooltip: root.m3colors.m3inverseSurface
        colOnTooltip: root.m3colors.m3inverseOnSurface
        colShadow: ColorUtils.transparentize(root.m3colors.m3shadow, 0.7)
        colOutline: root.m3colors.m3outline
    }

    rounding: AppearanceRounding {}

    font: AppearanceFont {}

    animationCurves: AppearanceAnimationCurves {}

    animation: AppearanceAnimation {
        elementMove: AppearanceMoveAnimation {
            duration: root.animationCurves.expressiveDefaultSpatialDuration
            bezierCurve: root.animationCurves.expressiveDefaultSpatial
        }

        elementMoveEnter: AppearanceMoveAnimation {
            duration: Common.Config.options.appearance.animation.duration.elementMoveEnter
            bezierCurve: root.animationCurves.emphasizedDecel
        }

        elementMoveFast: AppearanceMoveAnimation {
            duration: root.animationCurves.expressiveEffectsDuration
            bezierCurve: root.animationCurves.expressiveEffects
        }
    }

    sizes: AppearanceSizes {}
}
