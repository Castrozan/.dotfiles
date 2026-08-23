pragma ComponentBehavior: Bound

import QtQuick
import "." as Common

QtObject {
    readonly property list<real> expressiveDefaultSpatial: [0.38, 1.21, 0.22, 1.00, 1, 1]
    readonly property list<real> expressiveEffects: [0.34, 0.80, 0.34, 1.00, 1, 1]
    readonly property list<real> emphasizedDecel: [0.05, 0.7, 0.1, 1, 1, 1]
    readonly property real expressiveDefaultSpatialDuration: Common.Config.options.appearance.animation.duration.elementMove
    readonly property real expressiveEffectsDuration: Common.Config.options.appearance.animation.duration.elementMoveFast
}
