pragma Singleton

import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: machineFeaturesRoot

    property string hostname: ""

    readonly property bool hasKeyboardBacklight: hostname === "dellg15"

    FileView {
        id: hostnameFileView
        path: "/etc/hostname"
        blockLoading: true
        onLoaded: machineFeaturesRoot.hostname = text().trim()
    }
}
