pragma Singleton

import Quickshell
import QtQuick

Singleton {
    readonly property var spacing: QtObject {
        readonly property int smaller: 4
        readonly property int small: 8
        readonly property int normal: 12
        readonly property int large: 16
    }

    readonly property var padding: QtObject {
        readonly property int smaller: 4
        readonly property int small: 8
        readonly property int normal: 12
        readonly property int large: 16
    }

    readonly property var rounding: QtObject {
        readonly property int small: 8
        readonly property int normal: 12
        readonly property int large: 16
        readonly property int full: 999
        readonly property real scale: 1.0
    }

    readonly property var font: QtObject {
        readonly property var family: QtObject {
            readonly property string sans: "JetBrainsMono Nerd Font"
            readonly property string material: "Material Symbols Rounded"
            readonly property string clock: "JetBrainsMono Nerd Font"
        }

        readonly property var size: QtObject {
            readonly property int smaller: 9
            readonly property int small: 10
            readonly property int normal: 12
            readonly property int large: 14
            readonly property int larger: 16
            readonly property int extraLarge: 20
        }
    }

    readonly property var anim: QtObject {
        readonly property var durations: QtObject {
            readonly property int small: 150
            readonly property int normal: 250
            readonly property int large: 400
            readonly property int extraLarge: 1000
            readonly property int expressiveDefaultSpatial: 500
            readonly property int expressiveFastSpatial: 200
        }

        readonly property var curves: QtObject {
            readonly property var standard: [0.2, 0.0, 0, 1.0, 1, 1]
            readonly property var standardAccel: [0.3, 0, 0.8, 0.15, 1, 1]
            readonly property var standardDecel: [0.05, 0.7, 0.1, 1.0, 1, 1]
            readonly property var emphasized: [0.2, 0, 0, 1.0, 1, 1]
            readonly property var expressiveDefaultSpatial: [0.34, 0, 0, 1, 1, 1]
            readonly property var expressiveFastSpatial: [0.1, 0, 0, 1, 1, 1]
        }
    }
}
