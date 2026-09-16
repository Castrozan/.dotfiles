pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import "functions"
import "appearance/colors"
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
            if (!loaded)
                return;
            root.applyHyprTheme();
        }
    }

    function applyHyprTheme() {
        if (!hyprThemeFile.loaded)
            return;
        try {
            const theme = JSON.parse(hyprThemeFile.text());
            PaletteMapping.applyHyprTheme(theme, hyprThemeColors);

            root.hyprThemeLoaded = true;
        } catch (e) {
            console.warn("overview: failed to parse hypr-theme colors", e);
        }
    }

    property MaterialColorScheme hyprThemeColors: FallbackMaterialPalette {
        defaults: root.defaultColors
        darkmode: true
    }

    property MaterialColorScheme defaultColors: DefaultMaterialPalette {}

    property MaterialColorScheme caelestiaColors: FallbackMaterialPalette {
        defaults: root.defaultColors
    }

    function loadCaelestiaPalette() {
        getCaelestiaScheme.running = true;
    }

    CaelestiaSchemeProcess {
        id: getCaelestiaScheme
        onPaletteUnavailable: root.caelestiaPaletteLoaded = false
        onPaletteRead: (palette, mode) => {
            const normalized = JSON.stringify({
                mode: mode,
                palette: palette,
                profile: root.caelestiaAccentProfile
            });
            if (normalized === root.lastCaelestiaPayload)
                return;
            root.lastCaelestiaPayload = normalized;
            PaletteMapping.applyCaelestiaPalette(palette, mode, root.caelestiaAccentProfile, root.defaultColors, root.caelestiaColors);
            root.caelestiaPaletteLoaded = Object.keys(palette).length > 0;
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
