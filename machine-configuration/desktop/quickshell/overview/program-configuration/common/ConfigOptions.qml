pragma ComponentBehavior: Bound

import QtQuick

QtObject {
    id: root

    required property var userOptions

    function read(path, fallback) {
        const parts = path.split(".");
        let current = userOptions;

        for (const part of parts) {
            if (current === null || current === undefined || typeof current !== "object" || !(part in current)) {
                return fallback;
            }
            current = current[part];
        }

        return current === undefined || current === null ? fallback : current;
    }

    function readInt(path, fallback) {
        const value = read(path, fallback);
        const parsed = Number(value);
        return Number.isInteger(parsed) ? parsed : fallback;
    }

    function readReal(path, fallback) {
        const value = read(path, fallback);
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : fallback;
    }

    function readBool(path, fallback) {
        const value = read(path, fallback);
        return typeof value === "boolean" ? value : fallback;
    }

    function readString(path, fallback) {
        const value = read(path, fallback);
        if (typeof value !== "string")
            return fallback;

        const trimmed = value.trim();
        return trimmed.length > 0 ? trimmed : fallback;
    }

    component CaelestiaOptions: QtObject {
        property bool autoRefresh: root.readBool("appearance.caelestia.autoRefresh", true)
        property int refreshInterval: root.readInt("appearance.caelestia.refreshInterval", 2000)
        property string accentProfile: root.readString("appearance.caelestia.accentProfile", "vibrant")
    }

    component RoundingOptions: QtObject {
        property int unsharpen: root.readInt("appearance.rounding.unsharpen", 2)
        property int verysmall: root.readInt("appearance.rounding.verysmall", 8)
        property int small: root.readInt("appearance.rounding.small", 12)
        property int normal: root.readInt("appearance.rounding.normal", 17)
        property int large: root.readInt("appearance.rounding.large", 23)
        property int full: root.readInt("appearance.rounding.full", 9999)
        property int screenRounding: root.readInt("appearance.rounding.screenRounding", large)
        property int windowRounding: root.readInt("appearance.rounding.windowRounding", 18)
    }

    component FontFamilyOptions: QtObject {
        property string main: root.readString("appearance.font.family.main", "sans-serif")
        property string title: root.readString("appearance.font.family.title", "sans-serif")
        property string expressive: root.readString("appearance.font.family.expressive", "sans-serif")
    }

    component FontPixelSizeOptions: QtObject {
        property int smaller: root.readInt("appearance.font.pixelSize.smaller", 12)
        property int small: root.readInt("appearance.font.pixelSize.small", 15)
        property int normal: root.readInt("appearance.font.pixelSize.normal", 16)
        property int larger: root.readInt("appearance.font.pixelSize.larger", 19)
        property int huge: root.readInt("appearance.font.pixelSize.huge", 22)
    }

    component FontOptions: QtObject {
        property FontFamilyOptions family: FontFamilyOptions {}
        property FontPixelSizeOptions pixelSize: FontPixelSizeOptions {}
    }

    component AnimationDurationOptions: QtObject {
        property int elementMove: root.readInt("appearance.animation.duration.elementMove", 500)
        property int elementMoveEnter: root.readInt("appearance.animation.duration.elementMoveEnter", 400)
        property int elementMoveFast: root.readInt("appearance.animation.duration.elementMoveFast", 200)
    }

    component AnimationOptions: QtObject {
        property AnimationDurationOptions duration: AnimationDurationOptions {}
    }

    component SizesOptions: QtObject {
        property real elevationMargin: root.readReal("appearance.sizes.elevationMargin", 10)
    }

    component AppearanceOptions: QtObject {
        property string colorSource: root.readString(
            "appearance.colorSource",
            root.readBool("appearance.useMatugenColors", false) ? "matugen" : "default"
        )
        property bool useMatugenColors: colorSource === "matugen"
        property CaelestiaOptions caelestia: CaelestiaOptions {}
        property RoundingOptions rounding: RoundingOptions {}
        property FontOptions font: FontOptions {}
        property AnimationOptions animation: AnimationOptions {}
        property SizesOptions sizes: SizesOptions {}
    }

    component OverviewEffectsOptions: QtObject {
        property bool enableBackdrop: root.readBool("overview.effects.enableBackdrop", false)
        property real backdropOpacity: root.readReal("overview.effects.backdropOpacity", 0.28)
        property real panelOpacity: root.readReal("overview.effects.panelOpacity", 0.92)
        property real workspaceOpacity: root.readReal("overview.effects.workspaceOpacity", 0.86)
        property real windowOverlayOpacity: root.readReal("overview.effects.windowOverlayOpacity", 0.22)
        property bool enableBlur: root.readBool("overview.effects.enableBlur", false)
        property bool glassMode: root.readBool("overview.effects.glassMode", false)
        property real glassTintStrength: root.readReal("overview.effects.glassTintStrength", 0.35)
        property real glassBorderOpacity: root.readReal("overview.effects.glassBorderOpacity", 0.72)
        property real glassShineOpacity: root.readReal("overview.effects.glassShineOpacity", 0.14)
    }

    component OverviewOptions: QtObject {
        property int rows: root.readInt("overview.rows", 2)
        property int columns: root.readInt("overview.columns", 5)
        property real scale: root.readReal("overview.scale", 0.16)
        property bool enable: root.readBool("overview.enable", true)
        property bool hideEmptyRows: root.readBool("overview.hideEmptyRows", true)
        property bool useWorkspaceMap: root.readBool("overview.useWorkspaceMap", false)
        property var workspaceMap: root.read("overview.workspaceMap", [])
        property bool orderRightLeft: root.readBool("overview.orderRightLeft", false)
        property bool orderBottomUp: root.readBool("overview.orderBottomUp", false)
        property bool previewsEnabled: root.readBool("overview.previewsEnabled", true)
        property string previewMode: root.readString("overview.previewMode", "live")
        property bool includeInactiveMonitorPreviews: root.readBool("overview.includeInactiveMonitorPreviews", true)
        property int previewRecaptureDelayMs: root.readInt("overview.previewRecaptureDelayMs", 60)
        property bool showSpecialWorkspaces: root.readBool("overview.showSpecialWorkspaces", true)
        property var specialWorkspaces: root.read("overview.specialWorkspaces", [])
        property int specialWorkspaceColumns: root.readInt("overview.specialWorkspaceColumns", columns)
        property real workspaceSpacing: root.readReal("overview.workspaceSpacing", 5)
        property real backgroundPadding: root.readReal("overview.backgroundPadding", 10)
        property real workspaceNumberBaseSize: root.readReal("overview.workspaceNumberBaseSize", 250)
        property OverviewEffectsOptions effects: OverviewEffectsOptions {}
    }

    component PositionOptions: QtObject {
        property int topMargin: root.readInt("position.topMargin", 100)
    }

    component WindowPreviewOptions: QtObject {
        property real iconToWindowRatio: root.readReal("windowPreview.iconToWindowRatio", 0.25)
        property real iconToWindowRatioCompact: root.readReal("windowPreview.iconToWindowRatioCompact", 0.45)
        property real xwaylandIndicatorToIconRatio: root.readReal("windowPreview.xwaylandIndicatorToIconRatio", 0.35)
        property real inactiveMonitorOpacity: root.readReal("windowPreview.inactiveMonitorOpacity", 0.4)
    }

    component HacksOptions: QtObject {
        property int arbitraryRaceConditionDelay: root.readInt("hacks.arbitraryRaceConditionDelay", 150)
        property int hyprlandEventDebounceMs: root.readInt("hacks.hyprlandEventDebounceMs", 40)
    }

    property AppearanceOptions appearance: AppearanceOptions {}
    property OverviewOptions overview: OverviewOptions {}
    property PositionOptions position: PositionOptions {}
    property WindowPreviewOptions windowPreview: WindowPreviewOptions {}
    property HacksOptions hacks: HacksOptions {}
}
