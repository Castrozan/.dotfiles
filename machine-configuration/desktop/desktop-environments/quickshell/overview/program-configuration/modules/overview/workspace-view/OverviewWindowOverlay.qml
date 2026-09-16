import QtQuick
import "../../../common"
import "../../../common/functions"

Rectangle {
    id: windowOverlay
    required property real previewScale
    required property bool pressed
    required property bool hovered
    required property real effectiveWindowOverlayOpacity
    required property bool glassMode
    required property real glassShineOpacity
    anchors.fill: parent
    radius: Appearance.rounding.windowRounding * windowOverlay.previewScale
    color: windowOverlay.pressed ? ColorUtils.applyAlpha(Appearance.colors.colLayer2Active, Math.min(1, windowOverlay.effectiveWindowOverlayOpacity + 0.30)) : windowOverlay.hovered ? ColorUtils.applyAlpha(Appearance.colors.colLayer2Hover, Math.min(1, windowOverlay.effectiveWindowOverlayOpacity + 0.20)) : ColorUtils.applyAlpha(windowOverlay.glassMode ? ColorUtils.mix(Appearance.colors.colLayer2, Appearance.colors.colLayer0, 0.38) : Appearance.colors.colLayer2, windowOverlay.effectiveWindowOverlayOpacity)
    border.color: windowOverlay.glassMode ? ColorUtils.applyAlpha(Appearance.m3colors.m3outline, 0.62) : ColorUtils.transparentize(Appearance.m3colors.m3outline, 0.7)
    border.width: 1

    Rectangle {
        visible: windowOverlay.glassMode
        anchors.fill: parent
        radius: parent.radius
        color: "transparent"
        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: ColorUtils.applyAlpha("#FFFFFF", windowOverlay.glassShineOpacity * 0.24)
            }
            GradientStop {
                position: 0.5
                color: ColorUtils.applyAlpha("#FFFFFF", 0.0)
            }
            GradientStop {
                position: 1.0
                color: ColorUtils.applyAlpha("#000000", windowOverlay.glassShineOpacity * 0.14)
            }
        }
    }

    Rectangle {
        visible: windowOverlay.glassMode
        anchors.fill: parent
        anchors.margins: 1
        radius: Math.max(parent.radius - 1, 0)
        color: "transparent"
        border.width: 1
        border.color: ColorUtils.applyAlpha("#FFFFFF", windowOverlay.glassShineOpacity * 0.32)
    }
}
