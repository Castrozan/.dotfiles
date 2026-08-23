pragma ComponentBehavior: Bound

import QtQuick
import "." as Common

QtObject {
    property int unsharpen: Common.Config.options.appearance.rounding.unsharpen
    property int verysmall: Common.Config.options.appearance.rounding.verysmall
    property int small: Common.Config.options.appearance.rounding.small
    property int normal: Common.Config.options.appearance.rounding.normal
    property int large: Common.Config.options.appearance.rounding.large
    property int full: Common.Config.options.appearance.rounding.full
    property int screenRounding: Common.Config.options.appearance.rounding.screenRounding
    property int windowRounding: Common.Config.options.appearance.rounding.windowRounding
}
