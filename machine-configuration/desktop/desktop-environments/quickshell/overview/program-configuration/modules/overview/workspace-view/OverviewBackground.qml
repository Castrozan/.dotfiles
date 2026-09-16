import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import "../../../common"
import "../../../services"
import ".."

Rectangle { // Background
    id: overviewBackground
    required property OverviewState overviewState
    property real padding: Config.options.overview.backgroundPadding
    anchors.fill: parent
    anchors.margins: Appearance.sizes.elevationMargin

    radius: Appearance.rounding.screenRounding * overviewBackground.overviewState.scale + padding
    clip: true
    color: ColorUtils.applyAlpha(overviewBackground.overviewState.glassMode ? ColorUtils.mix(Appearance.colors.colLayer0, Appearance.colors.colLayer1, 0.78 - overviewBackground.overviewState.glassTintStrength * 0.35) : Appearance.colors.colLayer0, overviewBackground.overviewState.effectivePanelOpacity)
    border.width: 1
    border.color: ColorUtils.applyAlpha(overviewBackground.overviewState.glassMode ? ColorUtils.mix(Appearance.colors.colLayer0Border, Appearance.m3colors.m3outline, 0.52) : Appearance.colors.colLayer0Border, overviewBackground.overviewState.glassMode ? overviewBackground.overviewState.glassBorderOpacity : overviewBackground.overviewState.effectivePanelOpacity)

    Rectangle {
        visible: overviewBackground.overviewState.glassMode
        anchors.fill: parent
        radius: parent.radius
        color: "transparent"
        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: ColorUtils.applyAlpha("#FFFFFF", overviewBackground.overviewState.glassShineOpacity * 0.35)
            }
            GradientStop {
                position: 0.42
                color: ColorUtils.applyAlpha("#FFFFFF", 0.0)
            }
            GradientStop {
                position: 1.0
                color: ColorUtils.applyAlpha("#000000", overviewBackground.overviewState.glassShineOpacity * 0.22)
            }
        }
    }

    Rectangle {
        visible: overviewBackground.overviewState.glassMode
        anchors.fill: parent
        anchors.margins: 1
        radius: Math.max(parent.radius - 1, 0)
        color: "transparent"
        border.width: 1
        border.color: ColorUtils.applyAlpha("#FFFFFF", overviewBackground.overviewState.glassBorderOpacity * 0.20)
    }
}
