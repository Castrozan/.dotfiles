import QtQuick.Layouts
import Quickshell.Io
import QtQuick
import "../../dashboard/components"
import "../../dashboard"

IconButton {
    property string iconName
    property string iconNameOff: iconName

    Layout.alignment: Qt.AlignHCenter

    icon: checked ? iconName : iconNameOff
    type: IconButton.Tonal
    toggle: true

    implicitWidth: 48
    implicitHeight: 48

    font.pointSize: Appearance.font.size.extraLarge
}
