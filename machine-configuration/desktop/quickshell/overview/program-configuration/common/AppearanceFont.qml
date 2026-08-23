pragma ComponentBehavior: Bound

import QtQuick
import "." as Common

QtObject {
    component Family: QtObject {
        property string main: Common.Config.options.appearance.font.family.main
        property string title: Common.Config.options.appearance.font.family.title
        property string expressive: Common.Config.options.appearance.font.family.expressive
    }

    component PixelSize: QtObject {
        property int smaller: Common.Config.options.appearance.font.pixelSize.smaller
        property int small: Common.Config.options.appearance.font.pixelSize.small
        property int normal: Common.Config.options.appearance.font.pixelSize.normal
        property int larger: Common.Config.options.appearance.font.pixelSize.larger
        property int huge: Common.Config.options.appearance.font.pixelSize.huge
    }

    property Family family: Family {}
    property PixelSize pixelSize: PixelSize {}
}
