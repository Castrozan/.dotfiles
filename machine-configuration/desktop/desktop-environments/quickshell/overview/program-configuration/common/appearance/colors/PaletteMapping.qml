pragma Singleton

import Quickshell
import "../../functions"

Singleton {
    function firstColor(palette, keys, fallback) {
        for (const key of keys) {
            if (palette[key])
                return palette[key];
        }
        return fallback;
    }

    function applyCaelestiaPalette(palette, mode, caelestiaAccentProfile, defaultColors, caelestiaColors) {
        if (caelestiaAccentProfile === "vibrant") {
            const primary = firstColor(palette, ["blue", "klink", "term12", "primary"], defaultColors.m3primary);
            const secondary = firstColor(palette, ["mauve", "lavender", "term13", "secondary"], defaultColors.m3secondary);
            const tertiary = firstColor(palette, ["pink", "rosewater", "term11", "tertiary"], defaultColors.m3secondaryContainer);
            const primaryContainer = firstColor(palette, ["sapphire", "klinkSelection", "primaryContainer"], defaultColors.m3primaryContainer);
            const secondaryContainer = firstColor(palette, ["surface2", "secondaryContainer"], defaultColors.m3secondaryContainer);

            caelestiaColors.m3primary = primary;
            caelestiaColors.m3onPrimary = ColorUtils.bestOnColor(primary);
            caelestiaColors.m3primaryContainer = primaryContainer;
            caelestiaColors.m3onPrimaryContainer = ColorUtils.bestOnColor(primaryContainer);
            caelestiaColors.m3secondary = secondary;
            caelestiaColors.m3onSecondary = ColorUtils.bestOnColor(secondary);
            caelestiaColors.m3secondaryContainer = secondaryContainer;
            caelestiaColors.m3onSecondaryContainer = ColorUtils.bestOnColor(secondaryContainer);
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

    function applyHyprTheme(theme, hyprThemeColors) {
        const bg = theme.background ?? "#161217";
        const fg = theme.foreground ?? "#EAE0E7";
        const primary = theme.primary ?? "#89b4fa";
        const accent = theme.accent ?? "#94e2d5";
        const dim = theme.dim ?? "#6c7086";
        const surface = theme.surface ?? "#45475a";

        hyprThemeColors.m3primary = primary;
        hyprThemeColors.m3onPrimary = ColorUtils.relativeLuminance(primary) > 0.5 ? "#121212" : "#f5f5f5";
        hyprThemeColors.m3primaryContainer = ColorUtils.mix(primary, bg, 0.3);
        hyprThemeColors.m3onPrimaryContainer = fg;
        hyprThemeColors.m3secondary = accent;
        hyprThemeColors.m3onSecondary = ColorUtils.relativeLuminance(accent) > 0.5 ? "#121212" : "#f5f5f5";
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
        hyprThemeColors.darkmode = ColorUtils.relativeLuminance(bg) < 0.5;
    }
}
