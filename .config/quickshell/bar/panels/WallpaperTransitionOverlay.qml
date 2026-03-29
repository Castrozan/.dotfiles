import Quickshell
import Quickshell.Wayland
import QtQuick
import Qt5Compat.GraphicalEffects
import "../dashboard"
import "../launcher/services"

PanelWindow {
    id: wallpaperTransitionOverlayRoot

    required property var screen

    property string previousWallpaperPath: ""
    property bool transitionActive: false
    property real circleDiameter: 0

    visible: transitionActive

    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }

    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: WlrLayer.Bottom
    WlrLayershell.namespace: "quickshell-wallpaper-transition"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None

    color: "transparent"
    surfaceFormat.opaque: false

    Image {
        id: previousWallpaperImage
        anchors.fill: parent
        source: wallpaperTransitionOverlayRoot.previousWallpaperPath !== ""
            ? `file://${wallpaperTransitionOverlayRoot.previousWallpaperPath}`
            : ""
        fillMode: Image.PreserveAspectCrop
        visible: false
        layer.enabled: true
    }

    Item {
        id: circleShrinkMask
        anchors.fill: parent
        visible: false
        layer.enabled: true

        Rectangle {
            anchors.centerIn: parent
            width: wallpaperTransitionOverlayRoot.circleDiameter
            height: wallpaperTransitionOverlayRoot.circleDiameter
            radius: wallpaperTransitionOverlayRoot.circleDiameter / 2
            color: "white"
            antialiasing: true
        }
    }

    OpacityMask {
        anchors.fill: parent
        source: previousWallpaperImage
        maskSource: circleShrinkMask
    }

    NumberAnimation {
        id: circleShrinkAnimation
        target: wallpaperTransitionOverlayRoot
        property: "circleDiameter"
        to: 0
        duration: 3000
        easing.type: Easing.BezierSpline
        easing.bezierCurve: Appearance.anim.curves.emphasized

        onFinished: {
            wallpaperTransitionOverlayRoot.transitionActive = false;
        }
    }

    function startTransition(oldWallpaperPath: string): void {
        circleShrinkAnimation.stop();
        previousWallpaperPath = oldWallpaperPath;
        circleDiameter = 4000;
        transitionActive = true;
    }

    function completeTransition(): void {
        circleDiameter = Math.sqrt(width * width + height * height);
        circleShrinkAnimation.from = circleDiameter;
        circleShrinkAnimation.start();
    }

    Connections {
        target: LauncherWallpapersService

        function onWallpaperChangeStarted(previousWallpaperPath: string): void {
            wallpaperTransitionOverlayRoot.startTransition(previousWallpaperPath);
        }

        function onWallpaperChangeApplied(): void {
            wallpaperTransitionOverlayRoot.completeTransition();
        }
    }
}
