pragma ComponentBehavior: Bound

import QtQuick
import "." as Common

QtObject {
    property real elevationMargin: Common.Config.options.appearance.sizes.elevationMargin
}
